from urllib import request
from tensorflow.keras.models import  Model
from PIL import Image
import numpy as np
import pandas as pd
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import  Model
from flask import Flask, request, render_template

# Ham tien xu ly, chuyen doi hinh anh thanh tensor
def image_preprocess(img):
    img = img.resize((224,224))
    img = img.convert("RGB")
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    return x
  

# Ham trich xuat dac trung anh
def extract_vector(model, image_path):
    print("Xu ly : ", image_path)
    img = Image.open(image_path)
    img_tensor = image_preprocess(img)
    # Trich dac trung
    vector = model.predict(img_tensor)[0]
    # Chuan hoa vector = chia chia L2 norm (tu google search)
    vector = vector / np.linalg.norm(vector)
    return vector

# Ham tao model
def get_extract_model():
    vgg16_model = VGG16(weights="imagenet")
    extract_model = Model(inputs=vgg16_model.inputs, outputs = vgg16_model.get_layer("fc1").output)
    return extract_model

# Đọc vectors từ file csv
global_df_vectors = pd.read_csv('./static/feature/clusters.csv')
# Đọc centroids từ file csv
global_centroids = pd.read_csv('./static/feature/centroids.csv')

#Tra cứu ảnh và đánh giá 
def evaluate(image_test,global_df_vectors, global_centroids):
  # Khoi tao model
  model = get_extract_model()
  # Trich dac trung anh search
  search_vector = extract_vector(model,image_test)
  # Đọc vectors từ file csv
  df_vectors = global_df_vectors
  # Đọc centroids từ file csv
  centroids = global_centroids
  # So sánh features của ảnh query với centroid features
  distance = np.linalg.norm(np.array(centroids[centroids.columns[0:4096]])- search_vector, axis=1)

  #Lấy tên cluster min
  min_cluster = list(distance).index(np.min(distance))

  #Lấy ra cluster giống với ảnh query được chọn
  df_vectors = df_vectors[df_vectors["cluster"]== min_cluster]
  #Ranking lại cluster
  distance = np.linalg.norm(np.array(df_vectors[df_vectors.columns[0:4096]])- search_vector, axis=1)
  df_vectors['distance'] = pd.Series(distance, index=df_vectors.index)
  df_vectors['rank'] = df_vectors['distance'].rank(ascending = 1)
  df_vectors = df_vectors.set_index('rank')
  df_vectors = df_vectors.sort_index()

  #Lấy ra cluster giống với ảnh query được chọn
  df_vect = df_vectors[df_vectors["cluster"]== min_cluster]
  #Ranking lại cluster
  distance = np.linalg.norm(np.array(df_vect[df_vect.columns[0:4096]])- search_vector, axis=1)
  df_vect['distance'] = pd.Series(distance, index=df_vect.index)
  df_vect['rank'] = df_vect['distance'].rank(ascending = 1)
  df_vect = df_vect.set_index('rank')
  df_vect = df_vect.sort_index()

  #Lấy ra kết quả ảnh giống nhất với ảnh query trong cluster
  result = df_vect[0:4] 

  content_compare = []
  for content in result['Content']: 
    content_compare.append(content)
    
  result['Content_compare'] = pd.Series(content_compare, index=result.index)
 
 
  return result

#build web Flask
main = Flask(__name__)
@main.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        file = request.files['query_img']
        # Save query image
        img = Image.open(file)  # PIL image
        uploaded_img_path = "static/uploaded/"+ file.filename
        img.save(uploaded_img_path)
     
        result = evaluate(uploaded_img_path, global_df_vectors, global_centroids)
        # Lấy kết quả và gửi đến html
        rs = result[['Path','Content_compare']]  
        rs = rs.to_records(index=False)
        rs = list(rs)
        return render_template('index.html',
                            query_path=uploaded_img_path,
                            scores=rs,
                            )
    else:
        return render_template('index.html')

if __name__=="__main__":
    main.run(debug=True)
