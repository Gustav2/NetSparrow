import argparse
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

def preprocess_data(data):
    """
    Preprocess the packet data for the model. Ensures the output shape matches the model's input.
    """
    print("Available columns in data:", data.columns)

    # Define columns based on the notebook and total expected features
    categorical_columns = [6, 11]  # Example: protocol and connection state
    numerical_columns = [8, 9, 10, 14, 16, 17]  # Example: duration, bytes

    # Ensure numerical columns are clean
    data.iloc[:, numerical_columns] = (
        data.iloc[:, numerical_columns]
        .replace(['-', '(empty)'], 0)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    # Handle categorical columns
    data.iloc[:, categorical_columns] = data.iloc[:, categorical_columns].replace(['-', '(empty)'], 'unknown')

    # Scale numeric data
    scaler = StandardScaler()
    scaled_numeric = scaler.fit_transform(data.iloc[:, numerical_columns])

    # Encode categorical data
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoded_categorical = encoder.fit_transform(data.iloc[:, categorical_columns])

    # Combine processed data
    processed_data = pd.concat(
        [
            pd.DataFrame(scaled_numeric, index=data.index),
            pd.DataFrame(encoded_categorical, index=data.index)
        ],
        axis=1
    )

    # Ensure the final shape matches the model's expected input
    required_features = 20
    if processed_data.shape[1] < required_features:
        # Add padding columns if too few features
        padding = pd.DataFrame(
            0, index=processed_data.index, columns=range(required_features - processed_data.shape[1])
        )
        processed_data = pd.concat([processed_data, padding], axis=1)
    elif processed_data.shape[1] > required_features:
        # Trim excess columns if too many features
        processed_data = processed_data.iloc[:, :required_features]

    return processed_data



def load_model(model_path):
    """
    Loads the trained Keras model.
    """
    return tf.keras.models.load_model(model_path)

def analyze_packets(input_file, model, output_file):
    """
    Analyze packets using the trained model and save the results to a CSV.
    """
    # Load packet data without headers
    data = pd.read_csv(input_file, header=None)

    # Assign column positions for source and destination IPs
    src_ips = data.iloc[:, 2]  # Column 3 (0-based index)
    dest_ips = data.iloc[:, 4]  # Column 5 (0-based index)

    # Preprocess the data for the model
    preprocessed_data = preprocess_data(data)

    # Predict confidence scores
    predictions = model.predict(preprocessed_data)
    confidences = predictions.squeeze()  # Flatten the predictions array

    # Create output DataFrame
    output_data = pd.DataFrame({
        "src_ip": src_ips,
        "dest_ip": dest_ips,
        "confidence": confidences
    })

    # Save to CSV
    output_data.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")



def main():
    parser = argparse.ArgumentParser(description="Analyze network packets using a pre-trained Keras model.")
    parser.add_argument("input", type=str, help="Path to the input CSV file containing packet data.")
    parser.add_argument("model", type=str, help="Path to the trained Keras model file.")
    parser.add_argument("output", type=str, help="Path to save the output CSV file.")
    
    args = parser.parse_args()
    
    # Load model
    model = load_model(args.model)
    
    # Analyze packets
    analyze_packets(args.input, model, args.output)

if __name__ == "__main__":
    main()
