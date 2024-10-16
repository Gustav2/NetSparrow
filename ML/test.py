import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras import regularizers
import xgboost as xgb
from sklearn.decomposition import PCA
from sklearn import tree
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn import metrics
import pyshark

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

# Load training data
data_train = pd.read_csv('data/KDDTrain+.txt')

columns = (
['duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes', 'land', 'wrong_fragment', 'urgent',
 'hot', 'num_failed_logins', 'logged_in', 'num_compromised', 'root_shell', 'su_attempted', 'num_root',
 'num_file_creations', 'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login', 'is_guest_login',
 'count', 'srv_count', 'serror_rate', 'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate', 'same_srv_rate',
 'diff_srv_rate', 'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate', 'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
 'dst_host_srv_serror_rate', 'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'outcome', 'level'])

data_train.columns = columns
data_train.loc[data_train['outcome'] == "normal", "outcome"] = 'normal'
data_train.loc[data_train['outcome'] != 'normal', "outcome"] = 'attack'

cat_cols = ['is_host_login', 'protocol_type', 'service', 'flag', 'land', 'logged_in', 'is_guest_login', 'level',
            'outcome']


def Scaling(df_num, cols):
    std_scaler = RobustScaler()
    std_scaler_temp = std_scaler.fit_transform(df_num)
    std_df = pd.DataFrame(std_scaler_temp, columns=cols)
    return std_df


def preprocess_with_padding(dataframe, original_columns):
    # Preprocess the data as usual
    dataframe['protocol_type'] = dataframe['protocol_type'].astype('category').cat.codes
    df_num = dataframe.drop(cat_cols, axis=1, errors='ignore')
    num_cols = df_num.columns
    scaled_df = Scaling(df_num, num_cols)
    dataframe.drop(labels=num_cols, axis="columns", inplace=True)
    dataframe[num_cols] = scaled_df[num_cols]

    # Convert 'outcome' to binary labels
    dataframe.loc[dataframe['outcome'] == "normal", "outcome"] = 0
    dataframe.loc[dataframe['outcome'] != 0, "outcome"] = 1

    dataframe = pd.get_dummies(dataframe, columns=['protocol_type', 'service', 'flag'], drop_first=True)

    # Add missing columns from the original training data
    for col in original_columns:
        if col not in dataframe.columns:
            dataframe[col] = 0

    # Ensure the columns are in the same order
    dataframe = dataframe[original_columns]
    return dataframe


# Preprocess training data
def preprocess(dataframe):
    df_num = dataframe.drop(cat_cols, axis=1)
    num_cols = df_num.columns
    scaled_df = Scaling(df_num, num_cols)
    dataframe.drop(labels=num_cols, axis="columns", inplace=True)
    dataframe[num_cols] = scaled_df[num_cols]

    dataframe.loc[dataframe['outcome'] == "normal", "outcome"] = 0
    dataframe.loc[dataframe['outcome'] != 0, "outcome"] = 1

    dataframe = pd.get_dummies(dataframe, columns=['protocol_type', 'service', 'flag'])
    return dataframe


scaled_train = preprocess(data_train)
x = scaled_train.drop(['outcome', 'level'], axis=1).values.astype('float32')
y = scaled_train['outcome'].values.astype('int')
y_reg = scaled_train['level'].values

pca = PCA(n_components=20)
pca = pca.fit(x)
x_reduced = pca.transform(x)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

model = tf.keras.Sequential([
    tf.keras.layers.Dense(units=64, activation='relu', input_shape=(x_train.shape[1:]),
                          kernel_regularizer=regularizers.L1L2(l1=1e-5, l2=1e-4),
                          bias_regularizer=regularizers.L2(1e-4),
                          activity_regularizer=regularizers.L2(1e-5)),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(units=128, activation='relu',
                          kernel_regularizer=regularizers.L1L2(l1=1e-5, l2=1e-4),
                          bias_regularizer=regularizers.L2(1e-4),
                          activity_regularizer=regularizers.L2(1e-5)),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(units=512, activation='relu',
                          kernel_regularizer=regularizers.L1L2(l1=1e-5, l2=1e-4),
                          bias_regularizer=regularizers.L2(1e-4),
                          activity_regularizer=regularizers.L2(1e-5)),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(units=128, activation='relu',
                          kernel_regularizer=regularizers.L1L2(l1=1e-5, l2=1e-4),
                          bias_regularizer=regularizers.L2(1e-4),
                          activity_regularizer=regularizers.L2(1e-5)),
    tf.keras.layers.Dropout(0.4),
    tf.keras.layers.Dense(units=1, activation='sigmoid'),
])

model.compile(optimizer='adam', loss=tf.keras.losses.BinaryCrossentropy(from_logits=True), metrics=['accuracy'])
model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=1, verbose=1)

# Load the pcap file
capture = pyshark.FileCapture('data/2018-10-25-14-06-32-192.168.1.132.pcap')

# Process packets
packet_data = []
for packet in capture:
    try:
        packet_info = {
            'duration': float(packet.sniff_time.timestamp()),
            'protocol_type': packet.highest_layer,
            'service': packet.transport_layer if hasattr(packet, 'transport_layer') else 'unknown',
            'flag': packet.tcp.flags if hasattr(packet, 'tcp') else 0,
            'src_bytes': int(packet.length),
            'dst_bytes': 0,
            'land': 1 if packet.ip.src == packet.ip.dst else 0,
            # Add other fields as needed
            'outcome': 0,
            'level': 0
        }
        packet_data.append(packet_info)
    except AttributeError:
        continue

# Convert to DataFrame and preprocess
df = pd.DataFrame(packet_data)
original_feature_columns = list(scaled_train.drop(['outcome', 'level'], axis=1).columns)
preprocessed_new_data = preprocess_with_padding(df, original_feature_columns)
x_new = preprocessed_new_data.drop(['outcome', 'level'], axis=1, errors='ignore').values.astype('float32')

# Transform with PCA and make predictions
x_new_reduced = pca.transform(x_new)
predictions = model.predict(x_new_reduced)
predicted_outcomes = (predictions > 0.5).astype('int')

# Save predictions
df['predicted_outcome'] = predicted_outcomes
df.to_csv('data/predicted_new_data.csv', index=False)

print("Predictions saved to 'data/predicted_new_data.csv'")
