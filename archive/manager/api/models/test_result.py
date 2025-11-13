from datetime import datetime
from . import db

class TestResult(db.Model):
    __tablename__ = 'test_results'

    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(100), nullable=False, index=True)
    test_type = db.Column(db.String(50), nullable=False, index=True)
    test_host = db.Column(db.String(255))
    test_server_ip = db.Column(db.String(45))
    test_client_ip = db.Column(db.String(45), index=True)

    avg_latency = db.Column(db.Float)
    avg_throughput = db.Column(db.Float)
    avg_jitter = db.Column(db.Float)
    avg_packet_loss = db.Column(db.Float)

    raw_results = db.Column(db.JSON)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='test_results')

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Convert test result to dictionary"""
        return {
            'id': self.id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'test_host': self.test_host,
            'test_server_ip': self.test_server_ip,
            'test_client_ip': self.test_client_ip,
            'avg_latency': self.avg_latency,
            'avg_throughput': self.avg_throughput,
            'avg_jitter': self.avg_jitter,
            'avg_packet_loss': self.avg_packet_loss,
            'raw_results': self.raw_results,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<TestResult {self.test_name} - {self.test_type}>'
