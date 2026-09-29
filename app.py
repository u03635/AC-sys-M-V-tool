from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    
    # 接收前端參數
    sys_type = data['sys_type']
    capacity_val = float(data['capacity_val'])
    capacity_unit = data['capacity_unit']
    
    temp_in = float(data['temp_in'])
    temp_out = float(data['temp_out'])
    measured_flow = float(data['measured_flow'])
    rated_power_kw = float(data['rated_power_kw'])
    measured_kw = float(data['measured_kw'])
    
    # 1. 單位換算：將所有銘牌冷凍能力輸入統一轉換為 USRT 基準
    if capacity_unit == 'usrt':
        rated_usrt = capacity_val
    elif capacity_unit == 'kcal_hr':
        rated_usrt = capacity_val / 3024.0
    elif capacity_unit == 'kw_cooling':
        rated_usrt = capacity_val / 3.516
    else:
        rated_usrt = capacity_val
        
    # 2. 現場溫差計算
    delta_t = abs(temp_in - temp_out)
    if delta_t == 0:
        return jsonify({"error": "溫差不可為零，請確認輸入數值。"})
    
    # 3. 理論流量計算 (LPM) - 採用標準設計溫差 5°C
    DESIGN_DELTA_T = 5.0
    if sys_type == 'chilled':
        # 冰水側：純冷凍能力
        theoretical_flow = (rated_usrt * 3024) / (60 * DESIGN_DELTA_T)
    else:
        # 冷卻水側：銘牌冷凍能力(kcal/hr) + 銘牌耗電作功(換算為 kcal/hr)
        # 捨棄 1.25 經驗值，以銘牌實際 kW 達到最高精準度
        theoretical_flow = ((rated_usrt * 3024) + (rated_power_kw * 860)) / (60 * DESIGN_DELTA_T)
        
    # 4. 流量誤差判定 (±10%)
    flow_error = (measured_flow - theoretical_flow) / theoretical_flow
    is_flow_valid = abs(flow_error) <= 0.10
    
    # 5. 效能與負載指標運算區塊
    # A. 計算現場實測冷凍能力 (Measured USRT)
    if sys_type == 'chilled':
        measured_usrt = (measured_flow * delta_t * 60) / 3024.0
    else:
        # 實測冷卻水側冷凍能力 = 實測總排熱量 - 實測壓縮機作功
        # 這裡直接使用電力分析儀的測量值 (measured_kw)
        measured_usrt = (measured_flow * delta_t * 60 / 3024.0) - (measured_kw / 3.516)
        
    # 防呆機制：避免除以零或出現負值
    safe_measured_usrt = measured_usrt if measured_usrt > 0 else 0.001
    safe_rated_usrt = rated_usrt if rated_usrt > 0 else 0.001
    safe_rated_power = rated_power_kw if rated_power_kw > 0 else 0.001

    # B. 量測運轉效率 (kW/RT)
    measured_efficiency = measured_kw / safe_measured_usrt
    
    # C. 額定運轉效率 (kW/RT)
    rated_efficiency = safe_rated_power / safe_rated_usrt
    
    # D. 量測耗電負載率 (%)
    power_load_ratio = measured_kw / safe_rated_power
    
    # E. 量測負載率 (冷凍能力負載率 %)
    cooling_load_ratio = safe_measured_usrt / safe_rated_usrt
    
    # F. 額定 COP
    rated_cop = (safe_rated_usrt * 3.516) / safe_rated_power
    
    return jsonify({
        "delta_t": round(delta_t, 2),
        "theoretical_flow": round(theoretical_flow, 0),
        "flow_error_percent": round(flow_error * 100, 1),
        "is_flow_valid": is_flow_valid,
        "measured_efficiency": round(measured_efficiency, 3),
        "rated_efficiency": round(rated_efficiency, 3),
        "power_load_ratio": round(power_load_ratio * 100, 1),
        "cooling_load_ratio": round(cooling_load_ratio * 100, 1),
        "rated_cop": round(rated_cop, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)
