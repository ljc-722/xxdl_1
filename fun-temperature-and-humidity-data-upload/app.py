import datetime  
from sanic import Sanic  
from sanic.response import json  

app = Sanic("Myapp")  

# 温度阈值  
t_threshold = (25, 28)  
# 湿度阈值  
h_threshold = (30, 33)  

@app.route("/upload", methods=["POST"],name='upload')  
@app.route("/invoke", methods=["POST"],name='invoke')  
def data_upload(request):  
    try:  
        # 尝试解析请求体为JSON  
        data = request.json  
        if data is None:  
            return json({"error": "请求体不是有效的JSON"}, status=400)  

        sn = data.get("sn")  
        temperature = data.get("temperature")  
        humidity = data.get("humidity")  

        if not all([sn, temperature, humidity]):  
            return json({"error": "参数错误"}, status=400)  

        # 检查温度和湿度是否超出阈值  
        t_out_flag = not (t_threshold[0] <= temperature <= t_threshold[1])  
        h_out_flag = not (h_threshold[0] <= humidity <= h_threshold[1])  

        email_body = generate_email_body(sn, temperature, humidity, t_threshold, h_threshold)  

        if not t_out_flag and not h_out_flag:  
            return json({"status": 0, "message": "正常", "data": None})

        log_data={
            "timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "log_level":"ERROR",
            "message":email_body
        }

        import requests
        # 日志生产者的内网访问地址
        requests.post("https://cn-hangproducer-lhhcrgwsvd.cn-hangzhou-vpc.sae.run/produce",json=log_data)

        res = {  
            "status": 1,  
            "message": "异常",  
            "data": {  
                "action":"send_email",
                "data":{
                    "recipient": "318341420@qq.com",  
                    "subject": "告警邮件-温湿度异常",  
                    "body": email_body
                    }
            } if t_out_flag or h_out_flag else None  
        }  

        return json(res)  
    except Exception as e:  
        return json({"error": str(e)}, status=500)  

def generate_email_body(sn, temperature, humidity, t_threshold, h_threshold):  
    return (  
        f"告警通知:\n\n"  
        f"当前设备{sn}超出温湿度范围\n\n"  
        f"当前温度: {temperature}°C\n"  
        f"当前温度阈值: {t_threshold[0]}°C - {t_threshold[1]}°C\n\n"  
        f"当前湿度: {humidity}%\n"  
        f"当前湿度阈值: {h_threshold[0]}% - {h_threshold[1]}%\n\n"  
        f"当前时间: {datetime.datetime.now().isoformat()}"  
    )  

if __name__ == "__main__":  
    app.run(host="0.0.0.0", port=9000)
