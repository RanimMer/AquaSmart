from plant_health_inference import predict_plant_health

img_path = r"C:\Users\ranim\Downloads\OIP (1).jpg"
label, conf = predict_plant_health(img_path)
print("Label:", label, "Confidence:", conf)
