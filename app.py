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
    usrt = float(data['usrt'])
    temp_in = float(data['temp_in'])
    temp_out = float(data['temp_out'])
    measured_flow = float(data['measured_flow'])
    rated_kw = float(data['rated_kw'])
    measured_kw = float(data['measured_kw'])
    
    # 1. 溫差計算
    delta_t = abs(temp_in - temp_out)
    if delta_t == 0:
        return jsonify({"error": "溫差不可為零，請確認輸入數值。"})
    
    # 2. 理論流量計算 (LPM)
    if sys_type == 'chilled':
        theoretical_flow = (usrt * 3024) / (60 * delta_t)
    else:
        # cooling water 考量 1.25 排熱係數
        theoretical_flow = (usrt * 3024 * 1.25) / (60 * delta_t)
        
    # 3. 流量誤差判定 (±10%)
    flow_error = (measured_flow - theoretical_flow) / theoretical_flow
    is_flow_valid = abs(flow_error) <= 0.10
    
    # 4. 電力誤差判定 (量測值 <= 額定值 * 1.1)
    is_power_valid = measured_kw <= (rated_kw * 1.10)
    power_ratio = measured_kw / rated_kw if rated_kw > 0 else 0
    
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
