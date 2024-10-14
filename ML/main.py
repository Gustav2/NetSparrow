import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import gradio as gr
import warnings
warnings.filterwarnings('ignore')


np.random.seed(0)
n = 100  # number of samples
features = ['packet_size', 'duration', 'protocol_type', 'num_packets', 'port_number']
target = 'traffic_type'

protocols = ['TCP', 'UDP', 'ICMP']# Generate random data for demonstration purposes
df = pd.DataFrame({
    'packet_size': np.random.randint(100, 1500, n),
    'duration': np.random.uniform(0, 120, n),  # Duration in seconds
    'protocol_type': np.random.choice(protocols, n),
    'num_packets': np.random.randint(1, 100, n),
    'port_number': np.random.randint(1, 65535, n),
    'traffic_type': np.random.choice(['normal', 'suspicious'], n)
})

df['protocol_type'] = df['protocol_type'].astype('category').cat.codes


X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)# Train a simple model
model = RandomForestClassifier()
model.fit(X_train, y_train)# Define the prediction function
def predict(packet_size, duration, protocol_type, num_packets, port_number):
    input_data = pd.DataFrame({
        'packet_size': [packet_size],
        'duration': [duration],
        'protocol_type': [protocols.index(protocol_type)],
        'num_packets': [num_packets],
        'port_number': [port_number]
    })
    prediction = model.predict(input_data)[0]
    return prediction


iface = gr.Interface(
    fn=predict,
    inputs=[
        gr.Number(label="Packet Size (Bytes)"),
        gr.Number(label="Duration (Seconds)"),
        gr.Dropdown(choices=protocols, label="Protocol Type"),
        gr.Number(label="Number of Packets"),
        gr.Number(label="Port Number")
    ],
    outputs=gr.Textbox(),
    title="AI based Network Traffic Analysis",
    description="Enter the details to analyze the network traffic"
)

iface.launch()