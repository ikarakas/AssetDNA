from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import io
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///asset_topology.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Environment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'SDE' or 'LABS'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class CisGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Asset(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    urn = db.Column(db.String(200), unique=True, nullable=False)
    environment = db.Column(db.String(50), nullable=False)
    cis_group = db.Column(db.String(100), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(45))
    operating_system = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'urn': self.urn,
            'environment': self.environment,
            'cisGroup': self.cis_group,
            'type': self.asset_type,
            'name': self.name,
            'location': self.location,
            'ipAddress': self.ip_address,
            'os': self.operating_system,
            'description': self.description,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

# Static asset types - these remain predefined for consistency
ASSET_TYPES = [
    'Server', 'Workstation', 'Laptop', 'Network Device', 
    'Storage', 'Virtual Machine', 'Container', 'Other'
]

def generate_asset_id():
    last_asset = Asset.query.order_by(Asset.id.desc()).first()
    if last_asset:
        last_num = int(last_asset.id.split('-')[1])
        return f"AST-{(last_num + 1):06d}"
    return "AST-001000"

def generate_urn(environment, cis_group, asset_name):
    org = 'myorg'
    env_code = re.sub(r'[^a-zA-Z0-9]', '', environment).lower()
    cis_code = re.sub(r'[^a-zA-Z0-9]', '', cis_group).lower()
    asset_code = re.sub(r'[^a-zA-Z0-9]', '', asset_name).lower()
    return f"urn:asset:{org}:{env_code}:{cis_code}:{asset_code}"

def get_environment_category(environment):
    # Check if environment exists in database
    env_obj = Environment.query.filter_by(name=environment).first()
    if env_obj:
        return env_obj.category
    
    # Fallback to hardcoded logic for backward compatibility
    lab_environments = ['MS1', 'FLEP SIL', 'ESM DBE', 'CONNECT LAB']
    return 'LABS' if environment in lab_environments else 'SDE'

@app.route('/')
def index():
    return render_template('index.html')

# Environment management endpoints
@app.route('/api/environments', methods=['GET'])
def get_environments():
    environments = Environment.query.all()
    return jsonify([env.to_dict() for env in environments])

@app.route('/api/environments', methods=['POST'])
def create_environment():
    data = request.json
    
    # Validate category
    if data['category'] not in ['SDE', 'LABS']:
        return jsonify({'error': 'Category must be SDE or LABS'}), 400
    
    environment = Environment(
        name=data['name'],
        category=data['category'],
        description=data.get('description', '')
    )
    
    db.session.add(environment)
    db.session.commit()
    
    return jsonify(environment.to_dict()), 201

@app.route('/api/environments/<int:env_id>', methods=['PUT'])
def update_environment(env_id):
    environment = Environment.query.get_or_404(env_id)
    data = request.json
    
    if 'category' in data and data['category'] not in ['SDE', 'LABS']:
        return jsonify({'error': 'Category must be SDE or LABS'}), 400
    
    environment.name = data.get('name', environment.name)
    environment.category = data.get('category', environment.category)
    environment.description = data.get('description', environment.description)
    
    db.session.commit()
    
    return jsonify(environment.to_dict())

@app.route('/api/environments/<int:env_id>', methods=['DELETE'])
def delete_environment(env_id):
    environment = Environment.query.get_or_404(env_id)
    
    # Check if environment is in use
    assets_using_env = Asset.query.filter_by(environment=environment.name).count()
    if assets_using_env > 0:
        return jsonify({'error': f'Cannot delete environment. {assets_using_env} assets are using it.'}), 400
    
    db.session.delete(environment)
    db.session.commit()
    
    return '', 204

# CIS Group management endpoints
@app.route('/api/cis-groups', methods=['GET'])
def get_cis_groups():
    cis_groups = CisGroup.query.all()
    return jsonify([group.to_dict() for group in cis_groups])

@app.route('/api/cis-groups', methods=['POST'])
def create_cis_group():
    data = request.json
    
    cis_group = CisGroup(
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(cis_group)
    db.session.commit()
    
    return jsonify(cis_group.to_dict()), 201

@app.route('/api/cis-groups/<int:group_id>', methods=['PUT'])
def update_cis_group(group_id):
    cis_group = CisGroup.query.get_or_404(group_id)
    data = request.json
    
    cis_group.name = data.get('name', cis_group.name)
    cis_group.description = data.get('description', cis_group.description)
    
    db.session.commit()
    
    return jsonify(cis_group.to_dict())

@app.route('/api/cis-groups/<int:group_id>', methods=['DELETE'])
def delete_cis_group(group_id):
    cis_group = CisGroup.query.get_or_404(group_id)
    
    # Check if CIS group is in use
    assets_using_group = Asset.query.filter_by(cis_group=cis_group.name).count()
    if assets_using_group > 0:
        return jsonify({'error': f'Cannot delete CIS group. {assets_using_group} assets are using it.'}), 400
    
    db.session.delete(cis_group)
    db.session.commit()
    
    return '', 204

# Asset types endpoint
@app.route('/api/asset-types')
def get_asset_types():
    return jsonify(ASSET_TYPES)

@app.route('/api/assets', methods=['GET'])
def get_assets():
    environment = request.args.get('environment')
    cis_group = request.args.get('cis_group')
    asset_type = request.args.get('type')
    search = request.args.get('search')
    
    query = Asset.query
    
    if environment:
        query = query.filter(Asset.environment == environment)
    if cis_group:
        query = query.filter(Asset.cis_group == cis_group)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if search:
        query = query.filter(
            db.or_(
                Asset.name.contains(search),
                Asset.description.contains(search),
                Asset.location.contains(search)
            )
        )
    
    assets = query.all()
    return jsonify([asset.to_dict() for asset in assets])

@app.route('/api/assets', methods=['POST'])
def create_asset():
    data = request.json
    
    asset_id = generate_asset_id()
    urn = generate_urn(data['environment'], data['cisGroup'], data['name'])
    
    asset = Asset(
        id=asset_id,
        urn=urn,
        environment=data['environment'],
        cis_group=data['cisGroup'],
        asset_type=data['type'],
        name=data['name'],
        location=data['location'],
        ip_address=data.get('ipAddress'),
        operating_system=data.get('os'),
        description=data.get('description')
    )
    
    db.session.add(asset)
    db.session.commit()
    
    return jsonify(asset.to_dict()), 201

@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    data = request.json
    
    if 'environment' in data or 'cisGroup' in data or 'name' in data:
        environment = data.get('environment', asset.environment)
        cis_group = data.get('cisGroup', asset.cis_group)
        name = data.get('name', asset.name)
        asset.urn = generate_urn(environment, cis_group, name)
    
    asset.environment = data.get('environment', asset.environment)
    asset.cis_group = data.get('cisGroup', asset.cis_group)
    asset.asset_type = data.get('type', asset.asset_type)
    asset.name = data.get('name', asset.name)
    asset.location = data.get('location', asset.location)
    asset.ip_address = data.get('ipAddress', asset.ip_address)
    asset.operating_system = data.get('os', asset.os)
    asset.description = data.get('description', asset.description)
    
    db.session.commit()
    
    return jsonify(asset.to_dict())

@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    db.session.delete(asset)
    db.session.commit()
    
    return '', 204

@app.route('/api/assets/move', methods=['POST'])
def move_asset():
    data = request.json
    asset = Asset.query.get_or_404(data['assetId'])
    
    if 'environment' in data:
        asset.environment = data['environment']
    if 'cisGroup' in data:
        asset.cis_group = data['cisGroup']
    
    asset.urn = generate_urn(asset.environment, asset.cis_group, asset.name)
    
    db.session.commit()
    
    return jsonify(asset.to_dict())

@app.route('/api/topology')
def get_topology():
    assets = Asset.query.all()
    
    topology = {
        'SDE': {},
        'LABS': {}
    }
    
    for asset in assets:
        category = get_environment_category(asset.environment)
        
        if asset.environment not in topology[category]:
            topology[category][asset.environment] = {}
        
        if asset.cis_group not in topology[category][asset.environment]:
            topology[category][asset.environment][asset.cis_group] = []
        
        topology[category][asset.environment][asset.cis_group].append(asset.to_dict())
    
    return jsonify(topology)

@app.route('/api/export/json')
def export_json():
    assets = Asset.query.all()
    data = [asset.to_dict() for asset in assets]
    
    output = io.StringIO()
    json.dump(data, output, indent=2)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name='assetdna.json'
    )

@app.route('/api/export/jsonl')
def export_jsonl():
    assets = Asset.query.all()
    
    output = io.StringIO()
    for asset in assets:
        json.dump(asset.to_dict(), output)
        output.write('\n')
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name='assetdna.jsonl'
    )

@app.route('/api/stats')
def get_stats():
    total_assets = Asset.query.count()
    environments = db.session.query(Asset.environment).distinct().count()
    cis_groups = db.session.query(Asset.cis_group).distinct().count()
    
    return jsonify({
        'totalAssets': total_assets,
        'totalEnvironments': environments,
        'totalCISGroups': cis_groups
    })

def init_sample_data():
    # Initialize default environments if none exist
    if Environment.query.count() == 0:
        default_environments = [
            {'name': 'NSUSS/NMT SDE', 'category': 'SDE', 'description': 'NSUSS/NMT Software Development Environment'},
            {'name': 'FLEP SDE', 'category': 'SDE', 'description': 'FLEP Software Development Environment'},
            {'name': 'MS1', 'category': 'LABS', 'description': 'MS1 Laboratory Environment'},
            {'name': 'FLEP SIL', 'category': 'LABS', 'description': 'FLEP Software-in-the-Loop Laboratory'},
            {'name': 'ESM DBE', 'category': 'LABS', 'description': 'ESM Database Environment'},
            {'name': 'CONNECT LAB', 'category': 'LABS', 'description': 'Connectivity Testing Laboratory'}
        ]
        
        for env_data in default_environments:
            env = Environment(**env_data)
            db.session.add(env)
        
        db.session.commit()
        print("Default environments initialized!")
    
    # Initialize default CIS groups if none exist
    if CisGroup.query.count() == 0:
        default_cis_groups = [
            {'name': 'Network Infrastructure', 'description': 'Network devices and infrastructure components'},
            {'name': 'Cloud Infrastructure', 'description': 'Cloud-based services and virtual resources'},
            {'name': 'Research Equipment', 'description': 'Research and development equipment'},
            {'name': 'Connectivity Testing', 'description': 'Connectivity and network testing equipment'},
            {'name': 'Data Storage', 'description': 'Storage systems and data management'},
            {'name': 'Application Servers', 'description': 'Application hosting and server infrastructure'}
        ]
        
        for group_data in default_cis_groups:
            group = CisGroup(**group_data)
            db.session.add(group)
        
        db.session.commit()
        print("Default CIS groups initialized!")
    
    # Initialize sample assets if none exist
    if Asset.query.count() == 0:
        sample_assets = [
            {
                'environment': 'NSUSS/NMT SDE',
                'cis_group': 'Network Infrastructure',
                'asset_type': 'Server',
                'name': 'NSUSS-WEB-01',
                'location': 'Rack 3A, Building 1',
                'ip_address': '192.168.1.10',
                'operating_system': 'Ubuntu 18.04 LTS',
                'description': 'Main web server for NSUSS/NMT applications'
            },
            {
                'environment': 'NSUSS/NMT SDE',
                'cis_group': 'Network Infrastructure',
                'asset_type': 'Server',
                'name': 'NSUSS-DB-01',
                'location': 'Rack 3B, Building 1',
                'ip_address': '192.168.1.20',
                'operating_system': 'CentOS 7',
                'description': 'Primary database server'
            },
            {
                'environment': 'FLEP SDE',
                'cis_group': 'Cloud Infrastructure',
                'asset_type': 'Virtual Machine',
                'name': 'FLEP-API-01',
                'location': 'AWS us-east-1',
                'ip_address': '10.0.1.100',
                'operating_system': 'Ubuntu 22.04 LTS',
                'description': 'FLEP API microservice'
            },
            {
                'environment': 'MS1',
                'cis_group': 'Research Equipment',
                'asset_type': 'Server',
                'name': 'MS1-COMPUTE-01',
                'location': 'MS1 Lab, Rack 1',
                'ip_address': '172.16.1.10',
                'operating_system': 'RHEL 9',
                'description': 'High-performance computing server'
            },
            {
                'environment': 'CONNECT LAB',
                'cis_group': 'Connectivity Testing',
                'asset_type': 'Server',
                'name': 'CONNECT-SRV-01',
                'location': 'CONNECT LAB, Rack A1',
                'ip_address': '172.16.4.10',
                'operating_system': 'Ubuntu 22.04 LTS',
                'description': 'Connectivity testing server'
            }
        ]
        
        for asset_data in sample_assets:
            asset_id = generate_asset_id()
            urn = generate_urn(asset_data['environment'], asset_data['cis_group'], asset_data['name'])
            
            asset = Asset(
                id=asset_id,
                urn=urn,
                environment=asset_data['environment'],
                cis_group=asset_data['cis_group'],
                asset_type=asset_data['asset_type'],
                name=asset_data['name'],
                location=asset_data['location'],
                ip_address=asset_data['ip_address'],
                operating_system=asset_data['operating_system'],
                description=asset_data['description']
            )
            db.session.add(asset)
        
        db.session.commit()
        print("Sample data initialized!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_sample_data()
    
    app.run(debug=True, host='0.0.0.0', port=5050)