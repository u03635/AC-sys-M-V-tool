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
    capacity_unit = data['capacity_unit'] # 接收單位: usrt, kcal_hr, kw_cooling
    
    temp_in = float(data['temp_in'])
    temp_out = float(data['temp_out'])
    measured_flow = float(data['measured_flow'])
    rated_power_kw = float(data['rated_power_kw']) # 耗電功率
    measured_kw = float(data['measured_kw'])
    
    # 1. 單位換算：將所有冷凍能力輸入統一轉換為 USRT 基準
    if capacity_unit == 'usrt':
        usrt = capacity_val
    elif capacity_unit == 'kcal_hr':
        usrt = capacity_val / 3024.0
    elif capacity_unit == 'kw_cooling':
        usrt = capacity_val / 3.516
    else:
        usrt = capacity_val
        
    # 2. 溫差計算
    delta_t = abs(temp_in - temp_out)
    if delta_t == 0:
        return jsonify({"error": "溫差不可為零，請確認輸入數值。"})
    
    # 3. 理論流量計算 (LPM)
    if sys_type == 'chilled':
        theoretical_flow = (usrt * 3024) / (60 * delta_t)
    else:
        # cooling water 考量 1.25 排熱係數
        theoretical_flow = (usrt * 3024 * 1.25) / (60 * delta_t)
        
    # 4. 流量誤差判定 (±10%)
    flow_error = (measured_flow - theoretical_flow) / theoretical_flow
    is_flow_valid = abs(flow_error) <= 0.10
    
    # 5. 電力誤差判定 (量測耗電 <= 額定耗電 * 1.1)
    is_power_valid = measured_kw <= (rated_power_kw * 1.10)
    power_ratio = measured_kw / rated_power_kw if rated_power_kw > 0 else 0
    
    return jsonify({
        "delta_t": round(delta_t, 2),
        "theoretical_flow": round(theoretical_flow, 1),
        "flow_error_percent": round(flow_error * 100, 1),
        "is_flow_valid": is_flow_valid,
        "power_ratio_percent": round(power_ratio * 100, 1),
        "is_power_valid": is_power_valid
    })

if __name__ == '__main__':
    app.run(debug=True)
