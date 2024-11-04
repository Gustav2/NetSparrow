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

class Firewall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(10), nullable=False)
    blocked_packets = db.Column(db.Integer, nullable=False, default=0)
    uptime = db.Column(db.String(20), nullable=False, default="0 minutes")

    def __repr__(self):
        return f"Firewall('{self.status}', '{self.blocked_packets}', '{self.uptime}')"

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    speed = db.Column(db.Integer, nullable=False)
    latency = db.Column(db.Integer, nullable=False)
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
    status = Firewall.query.first()
    if not status:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({"status": status.status})

@app.route('/blocked_packets', methods=['GET'])
@require_appkey
def get_blocked_packets():
    blocked_packets = Firewall.query.first()
    if not blocked_packets:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({"blocked_packets": blocked_packets.blocked_packets})

@app.route('/uptime', methods=['GET'])
@require_appkey
def get_uptime():
    uptime = Firewall.query.first()
    if not uptime:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({"uptime": uptime.uptime})

@app.route('/blocked_packets', methods=['PATCH'])
@require_appkey
def update_blocked_packets():
    blocked_packets = Firewall.query.first()
    if not blocked_packets:
        return jsonify({"error": "No firewall status found"}), 404

    data = request.get_json()
    if 'blocked_packets' not in data:
        return jsonify({"error": "Invalid request"}), 400

    blocked_packets.blocked_packets = data['blocked_packets']
    db.session.commit()

    return jsonify({"message": "Blocked packets updated successfully"})

@app.route('/status', methods=['PATCH'])
@require_appkey
def update_status():
    status = Firewall.query.first()
    if not status:
        return jsonify({"error": "No firewall status found"}), 404

    data = request.get_json()
    if 'status' not in data:
        return jsonify({"error": "Invalid request"}), 400

    status.status = data['status']
    db.session.commit()

    return jsonify({"message": "Status updated successfully"})

# return all firewall status
@app.route('/firewall', methods=['GET'])
@require_appkey
def get_firewall():
    firewall = Firewall.query.first()
    if not firewall:
        return jsonify({"error": "No firewall status found"}), 404
    
    return jsonify({
        "status": firewall.status,
        "blocked_packets": firewall.blocked_packets,
        "uptime": firewall.uptime
    })

@app.route('/log', methods=['POST'])
@require_appkey
def add_log():
    data = request.get_json()
    if 'speed' not in data or 'latency' not in data or 'status' not in data:
        return jsonify({"error": "Invalid request"}), 400

    new_log = Log(speed=data['speed'], latency=data['latency'], status=data['status'])
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
            "status": log.status
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
    if not Firewall.query.first():
        # Create and add an initial record
        initial_status = Firewall(status="running", blocked_packets=325, uptime="0 hours")
        db.session.add(initial_status)
        db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000', debug=True)

# host='0.0.0.0', port='5000', 