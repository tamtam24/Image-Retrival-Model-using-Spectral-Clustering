import numpy as np
import pandas as pd
from sklearn.neighbors import kneighbors_graph
from scipy import sparse
from sklearn.cluster import KMeans
from scipy import linalg

# load data
df= pd.read_csv('./static/feature/features.csv') 
# phan cum features bang thuat toan spectral clustering

# 1/tinh ma tran lalapcian
def generate_graph_laplacian(df, nn):
    connectivity = kneighbors_graph(X=df, n_neighbors=nn, mode='connectivity')
    adjacency_matrix_w = (1/2)*(connectivity + connectivity.T)
    graph_laplacian_s = sparse.csgraph.laplacian(csgraph=adjacency_matrix_w, normed=False)
    graph_laplacian = graph_laplacian_s.toarray()
    return graph_laplacian 
# 2/tinh gia tri rieng, vector rieng
def compute_spectrum_graph_laplacian(graph_laplacian):
    eigenvals, eigenvcts = linalg.eig(graph_laplacian)
    eigenvals = np.real(eigenvals)
    eigenvcts = np.real(eigenvcts)
    return eigenvals, eigenvcts
# 3/chon k vector rieng dau tien
def project_and_transpose(eigenvals, eigenvcts, num_ev):
    eigenvals_sorted_indices = np.argsort(eigenvals)
    indices = eigenvals_sorted_indices[: num_ev]
    proj_df = pd.DataFrame(eigenvcts[:, indices.squeeze()])
    proj_df.columns = ['v_' + str(c) for c in proj_df.columns]
    return proj_df
# 4/phan cum voi kmeans
def run_k_means(df, n_clusters):
    k_means = KMeans(n_clusters=n_clusters)
    k_means.fit(df)
    cluster = k_means.predict(df)
    return cluster
#Spectral clustering
def spectral_clustering(df, n_neighbors, num_ev, n_clusters):
    graph_laplacian = generate_graph_laplacian(df, n_neighbors)
    eigenvals, eigenvcts = compute_spectrum_graph_laplacian(graph_laplacian)
    proj_df = project_and_transpose(eigenvals, eigenvcts, num_ev)
    cluster = run_k_means(proj_df, n_clusters)
    return cluster

cluster = spectral_clustering(df=df[df.columns[0:4096]], n_neighbors=40,num_ev=20, n_clusters=224)
df['cluster'] = pd.Series(cluster, index=df.index)

# Select only numeric columns for the mean calculation
numeric_cols = df.select_dtypes(include=[np.number]).columns
Centroids = df[numeric_cols].groupby(["cluster"]).mean()

df.to_csv("./static/feature/clusters.csv", index = False)
Centroids.to_csv("./static/feature/centroids.csv", index = False)