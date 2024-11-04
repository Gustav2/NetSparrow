from functools import wraps
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
API_KEY = "324155"


"""
    Database setup
"""
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///firewall.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    speed = db.Column(db.Integer, nullable=False)
    latency = db.Column(db.Integer, nullable=False)
    packets_blocked = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"Log('{self.timestamp}', '{self.speed}', '{self.latency}', '{self.status}')"

with app.app_context():
    db.create_all()


"""
    API key validation
"""
def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('x-api-key') and request.headers.get('x-api-key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized access"}), 401
    return decorated_function


"""
    API endpoints
"""
@app.route('/status', methods=['GET'])
@require_appkey
def get_status():
    status = Log.query.first()
    if not status:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({"status": status.status})

@app.route('/blocked_packets', methods=['GET'])
@require_appkey
def get_blocked_packets():
    # get sum of  all blocked packets in the log
    blocked_packets = Log.query.with_entities(db.func.sum(Log.packets_blocked)).first()
    if not blocked_packets:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({"blocked_packets": blocked_packets[0]})

@app.route('/log', methods=['POST'])
@require_appkey
def add_log():
    data = request.get_json()
    if 'speed' not in data or 'latency' not in data or 'status' not in data or 'packets_blocked' not in data:
        return jsonify({"error": "Invalid request"}), 400

    new_log = Log(speed=data['speed'], latency=data['latency'], status=data['status'], packets_blocked=data['packets_blocked'])

    if Log.query.count() >= 24:
        oldest_log = Log.query.order_by(Log.timestamp.asc()).first()
        db.session.delete(oldest_log)

    db.session.add(new_log)
    db.session.commit()

    return jsonify({"message": "Log added successfully"})

@app.route('/log', methods=['GET'])
@require_appkey
def get_logs():
    logs = Log.query.order_by(Log.timestamp.desc()).limit(24).all()
    if not logs:
        return jsonify({"error": "No logs found"}), 404

    logs_list = []
    for log in logs:
        logs_list.append({
            "timestamp": log.timestamp,
            "speed": log.speed,
            "latency": log.latency,
            "status": log.status,
            "packets_blocked": log.packets_blocked
        })

    return jsonify(logs_list)

@app.route('/latest_speed', methods=['GET'])
@require_appkey
def get_latest_speed():
    log = Log.query.order_by(Log.timestamp.desc()).first()
    if not log:
        return jsonify({"error": "No log found"}), 404
    
    return jsonify({"speed": log.speed})

@app.route('/latest_latency', methods=['GET'])
@require_appkey
def get_latest_latency():
    log = Log.query.order_by(Log.timestamp.desc()).first()
    if not log:
        return jsonify({"error": "No log found"}), 404
    
    return jsonify({"latency": log.latency})

with app.app_context():
    # Check if there are any records in the table
    if not Log.query.first():
        # Create and add an initial record
        initial_status = Log(status="running", speed=0, latency=0, packets_blocked=0)
        db.session.add(initial_status)
        db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)

# host='0.0.0.0', port='5000', 