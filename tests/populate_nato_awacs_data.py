#!/usr/bin/env python3
"""
NATO AWACS Test Data Population Script
Generates realistic asset hierarchy for NATO Airborne Warning and Control System
"""

import requests
import json
import random
from datetime import datetime, timedelta
import uuid

# API Configuration
API_BASE = "http://localhost:10001/api/v1"

# Asset Types for NATO AWACS Systems
ASSET_TYPES = [
    {"name": "Domain", "description": "Top-level operational domain"},
    {"name": "System", "description": "Major system or platform"},
    {"name": "Subsystem", "description": "System subdivision"},
    {"name": "Component", "description": "Individual component"},
    {"name": "Module", "description": "Software or hardware module"},
    {"name": "Service", "description": "Service or capability"},
    {"name": "Interface", "description": "System interface or API"},
    {"name": "Environment", "description": "Deployment environment"},
    {"name": "Facility", "description": "Physical facility or location"},
    {"name": "Network", "description": "Network infrastructure"},
    {"name": "Database", "description": "Database system"},
    {"name": "Application", "description": "Software application"},
    {"name": "Equipment", "description": "Hardware equipment"},
    {"name": "Sensor", "description": "Sensor or detector"},
    {"name": "Processor", "description": "Processing unit"}
]

class NATOAWACSDataGenerator:
    def __init__(self):
        self.asset_types = {}
        self.created_assets = []
        self.asset_count = 0
        
    def create_asset_types(self):
        """Create all asset types in the system"""
        print("Creating asset types...")
        
        # First, fetch all existing types
        response = requests.get(f"{API_BASE}/assets/types")
        if response.status_code == 200:
            for existing_type in response.json():
                self.asset_types[existing_type["name"]] = existing_type
                print(f"  ✓ Found existing asset type: {existing_type['name']}")
        
        # Create a mapping from our desired names to existing types
        # Respecting the hierarchy levels:
        # Level 1: Domain / System of Systems
        # Level 2: System / Environment, Subsystem / Service
        # Level 3: Subsystem
        # Level 4: Component / Segment
        # Level 5: Configuration Items (CI, Hardware CI, Software CI, Firmware CI)
        self.type_mapping = {
            "Domain": "Domain / System of Systems",  # Level 1
            "System": "System / Environment",  # Level 2
            "Subsystem": "Subsystem",  # Level 3
            "Component": "Component / Segment",  # Level 4
            "Module": "Component / Segment",  # Level 4 (not 5)
            "Service": "Subsystem / Service",  # Level 2
            "Interface": "Component / Segment",  # Level 4
            "Environment": "System / Environment",  # Level 2
            "Facility": "Subsystem",  # Level 3 (not 5)
            "Network": "Subsystem",  # Level 3
            "Database": "Component / Segment",  # Level 4
            "Application": "Component / Segment",  # Level 4
            "Equipment": "Component / Segment",  # Level 4
            "Sensor": "Hardware CI",  # Level 5
            "Processor": "Software CI"  # Level 5
        }
        
        # Now create any missing types
        for asset_type in ASSET_TYPES:
            if asset_type["name"] not in self.asset_types:
                response = requests.post(f"{API_BASE}/assets/types", json=asset_type)
                if response.status_code == 200:
                    self.asset_types[asset_type["name"]] = response.json()
                    print(f"  ✓ Created asset type: {asset_type['name']}")
                else:
                    print(f"  ✗ Failed to create asset type: {asset_type['name']}")
    
    def create_asset(self, name, asset_type, parent_id=None, description=None, metadata=None):
        """Create a single asset"""
        # Map our asset type name to the actual type in the system
        actual_type = self.type_mapping.get(asset_type, asset_type)
        if actual_type not in self.asset_types:
            print(f"  ✗ Unknown asset type: {asset_type} (mapped to {actual_type})")
            return None
            
        asset_data = {
            "name": name,
            "asset_type_id": self.asset_types[actual_type]["id"],
            "parent_id": parent_id,
            "description": description or f"{name} - {asset_type}",
            "status": random.choice(["active", "active", "active", "inactive"]),  # 75% active
            "external_id": f"NATO-{uuid.uuid4().hex[:8].upper()}",
            "properties": metadata or {}
        }
        
        response = requests.post(f"{API_BASE}/assets", json=asset_data)
        if response.status_code == 200:
            asset = response.json()
            self.created_assets.append(asset)
            self.asset_count += 1
            return asset
        else:
            print(f"  ✗ Failed to create asset: {name} - Status: {response.status_code}")
            if response.status_code != 200:
                print(f"    Error: {response.text[:200]}")
            return None
    
    def generate_nato_awacs_hierarchy(self):
        """Generate complete NATO AWACS asset hierarchy"""
        print("\nGenerating NATO AWACS asset hierarchy...")
        
        # Level 0: Top-level Domains
        domains = [
            ("NATO AWACS Operations", "Domain", {
                "classification": "NATO UNCLASSIFIED",
                "location": "Geilenkirchen, Germany",
                "established": "1982"
            }),
            ("E-3A Component", "Domain", {
                "fleet_size": "14 aircraft",
                "base": "NATO Air Base Geilenkirchen"
            })
        ]
        
        domain_assets = {}
        for name, asset_type, metadata in domains:
            asset = self.create_asset(name, asset_type, metadata=metadata)
            if asset:
                domain_assets[name] = asset
                print(f"  Created domain: {name}")
        
        # Level 1: Major Systems under NATO AWACS Operations
        if "NATO AWACS Operations" in domain_assets:
            parent_id = domain_assets["NATO AWACS Operations"]["id"]
            
            # Mission Systems
            mission_sys = self.create_asset("Mission Systems", "System", parent_id, 
                                           "Core mission execution systems")
            if mission_sys:
                self._create_mission_systems(mission_sys["id"])
            
            # Ground Systems
            ground_sys = self.create_asset("Ground Systems", "System", parent_id,
                                          "Ground-based support systems")
            if ground_sys:
                self._create_ground_systems(ground_sys["id"])
            
            # Training & Simulation
            training_sys = self.create_asset("Training & Simulation", "System", parent_id,
                                            "Training and simulation infrastructure")
            if training_sys:
                self._create_training_systems(training_sys["id"])
            
            # Command & Control
            c2_sys = self.create_asset("Command & Control", "System", parent_id,
                                      "C2 infrastructure and systems")
            if c2_sys:
                self._create_command_control_systems(c2_sys["id"])
        
        # Level 1: Technical Systems under E-3A Component
        if "E-3A Component" in domain_assets:
            parent_id = domain_assets["E-3A Component"]["id"]
            
            # Aircraft Systems
            aircraft_sys = self.create_asset("Aircraft Systems", "System", parent_id,
                                            "E-3A aircraft technical systems")
            if aircraft_sys:
                self._create_aircraft_systems(aircraft_sys["id"])
            
            # Support Infrastructure
            support_sys = self.create_asset("Support Infrastructure", "System", parent_id,
                                           "Technical support infrastructure")
            if support_sys:
                self._create_support_infrastructure(support_sys["id"])
    
    def _create_mission_systems(self, parent_id):
        """Create mission systems hierarchy"""
        # Mission Planning
        mp = self.create_asset("Mission Planning System", "Subsystem", parent_id,
                              "Comprehensive mission planning and execution")
        if mp:
            # Planning modules
            planning_modules = [
                "Route Planning Module",
                "Threat Assessment Module", 
                "Resource Allocation Module",
                "Weather Integration Module",
                "SIGINT Planning Module"
            ]
            for module in planning_modules:
                m = self.create_asset(module, "Module", mp["id"])
                if m and random.random() > 0.5:
                    # Add some components
                    for i in range(random.randint(2, 4)):
                        self.create_asset(f"{module} Component {i+1}", "Component", m["id"])
        
        # Surveillance Systems
        surv = self.create_asset("Surveillance Management System", "Subsystem", parent_id,
                                "Airborne surveillance coordination")
        if surv:
            # Radar systems
            radar = self.create_asset("Radar Control System", "Module", surv["id"])
            if radar:
                radar_components = [
                    "AN/APY-2 Radar Interface",
                    "Radar Data Processor",
                    "Target Tracking System",
                    "IFF Integration Module"
                ]
                for comp in radar_components:
                    self.create_asset(comp, "Component", radar["id"])
            
            # ESM systems
            esm = self.create_asset("ESM System", "Module", surv["id"])
            if esm:
                esm_components = [
                    "Signal Detection Unit",
                    "Emitter Identification System",
                    "Direction Finding Module",
                    "Electronic Order of Battle"
                ]
                for comp in esm_components:
                    self.create_asset(comp, "Component", esm["id"])
        
        # Data Links
        dl = self.create_asset("Data Link Systems", "Subsystem", parent_id,
                              "Tactical data link management")
        if dl:
            links = [
                ("Link 16 Terminal", "JTIDS/MIDS integration"),
                ("Link 11 System", "Legacy data link support"),
                ("Link 22 Gateway", "NATO extended data link"),
                ("JREAP Interface", "Beyond line-of-sight relay")
            ]
            for link_name, desc in links:
                link = self.create_asset(link_name, "Module", dl["id"], desc)
                if link:
                    # Add interfaces
                    for i in range(random.randint(2, 3)):
                        self.create_asset(f"{link_name} Interface {i+1}", "Interface", link["id"])
    
    def _create_ground_systems(self, parent_id):
        """Create ground systems hierarchy"""
        # Ground Entry Points
        gep = self.create_asset("Ground Entry Points", "Subsystem", parent_id,
                               "Ground-based communication entry points")
        if gep:
            # Multiple GEP locations
            gep_sites = [
                ("GEP Geilenkirchen", "Primary site"),
                ("GEP Uedem", "German site"),
                ("GEP Konya", "Turkish site"),
                ("GEP Trapani", "Italian site"),
                ("GEP Aktion", "Greek site"),
                ("GEP Oerland", "Norwegian site")
            ]
            for site_name, desc in gep_sites:
                site = self.create_asset(site_name, "Facility", gep["id"], desc)
                if site:
                    # Add GEP components
                    self._create_gep_components(site["id"], site_name)
        
        # Mission Support Systems
        mss = self.create_asset("Mission Support Systems", "Subsystem", parent_id,
                               "Ground-based mission support")
        if mss:
            support_systems = [
                "Flight Following System",
                "Mission Data Archive",
                "Intelligence Database System",
                "Mission Debrief System",
                "Performance Analysis Tool"
            ]
            for sys in support_systems:
                s = self.create_asset(sys, "Application", mss["id"])
                if s:
                    # Add databases
                    self.create_asset(f"{sys} Database", "Database", s["id"])
        
        # Network Operations Center
        noc = self.create_asset("Network Operations Center", "Subsystem", parent_id,
                               "Central network management")
        if noc:
            # Add NOC components directly
            noc_components = [
                "Network Monitoring System",
                "Performance Management",
                "Configuration Management",
                "Fault Management System",
                "Security Monitoring"
            ]
            for comp in noc_components:
                self.create_asset(comp, "Application", noc["id"])
    
    def _create_gep_components(self, parent_id, site_name):
        """Create GEP site components"""
        # Communication systems
        comm = self.create_asset(f"{site_name} Comm Systems", "Module", parent_id)
        if comm:
            comm_components = [
                "SATCOM Terminal",
                "HF Radio System",
                "VHF/UHF Radio",
                "Fiber Optic Interface",
                "Microwave Link"
            ]
            for comp in comm_components:
                self.create_asset(f"{comp}", "Equipment", comm["id"])
        
        # Processing systems
        proc = self.create_asset(f"{site_name} Processing", "Module", parent_id)
        if proc:
            proc_components = [
                "Data Processing Server",
                "Encryption Gateway",
                "Protocol Converter",
                "Message Handler"
            ]
            for comp in proc_components:
                # Create as Component (level 4) since Module is also level 4
                self.create_asset(f"{comp}", "Component", proc["id"])
    
    def _create_training_systems(self, parent_id):
        """Create training and simulation systems"""
        # Simulation Center
        sim = self.create_asset("E-3A Simulation Center", "Subsystem", parent_id,
                               "Full mission simulation facility")
        if sim:
            # Mission Crew Trainer
            mct = self.create_asset("Mission Crew Trainer", "Module", sim["id"],
                                   "Full-fidelity crew training system")
            if mct:
                crew_positions = [
                    "Surveillance Console Sim",
                    "Weapons Director Sim",
                    "Communications Sim",
                    "ESM Operator Sim",
                    "Data Link Controller Sim",
                    "Mission Commander Sim"
                ]
                for pos in crew_positions:
                    p = self.create_asset(pos, "Component", mct["id"])
                    if p:
                        # Add workstation
                        self.create_asset(f"{pos} Workstation", "Equipment", p["id"])
            
            # Scenario Generator
            scenario = self.create_asset("Scenario Generation System", "Module", sim["id"])
            if scenario:
                scenario_components = [
                    "Air Scenario Builder",
                    "Ground Forces Editor",
                    "Electronic Warfare Sim",
                    "Weather Effects Generator"
                ]
                for comp in scenario_components:
                    self.create_asset(comp, "Application", scenario["id"])
        
        # Computer-Based Training
        cbt = self.create_asset("CBT Systems", "Subsystem", parent_id,
                               "Computer-based training infrastructure")
        if cbt:
            courses = [
                "Basic AWACS Operations",
                "Advanced Surveillance Techniques",
                "Data Link Management",
                "ESM Operations",
                "Mission Planning Procedures"
            ]
            for course in courses:
                self.create_asset(f"{course} Course", "Application", cbt["id"])
    
    def _create_command_control_systems(self, parent_id):
        """Create command and control systems"""
        # Operations Center
        ops = self.create_asset("Operations Center", "Subsystem", parent_id,
                               "24/7 operations management")
        if ops:
            # Battle Management
            bm = self.create_asset("Battle Management System", "Module", ops["id"])
            if bm:
                bm_components = [
                    "Air Picture Compilation",
                    "Track Management System",
                    "Identification System",
                    "Threat Evaluation Module",
                    "Weapons Assignment"
                ]
                for comp in bm_components:
                    c = self.create_asset(comp, "Component", bm["id"])
                    if c and random.random() > 0.6:
                        # Add services
                        for i in range(random.randint(1, 3)):
                            self.create_asset(f"{comp} Service {i+1}", "Service", c["id"])
        
        # System Integration Lab
        sil = self.create_asset("System Integration Lab", "Subsystem", parent_id,
                               "System testing and integration facility")
        if sil:
            self._create_sil_components(sil["id"])
        
        # Crypto Management
        crypto = self.create_asset("Crypto Management System", "Subsystem", parent_id,
                                  "Cryptographic key management")
        if crypto:
            crypto_components = [
                "Key Distribution Center",
                "Certificate Authority",
                "HSM Infrastructure",
                "Crypto Audit System"
            ]
            for comp in crypto_components:
                self.create_asset(comp, "Module", crypto["id"])
    
    def _create_sil_components(self, parent_id):
        """Create System Integration Lab components"""
        # Test environments
        environments = [
            ("Development Environment", "Development and unit testing"),
            ("Integration Environment", "System integration testing"),
            ("Pre-Production Environment", "Pre-deployment validation"),
            ("Training Environment", "Training and exercises")
        ]
        
        for env_name, desc in environments:
            env = self.create_asset(env_name, "Environment", parent_id, desc)
            if env:
                # Add test systems
                test_systems = [
                    "Test Radar Simulator",
                    "Data Link Test Set",
                    "Network Emulator",
                    "Load Generator",
                    "Protocol Analyzer"
                ]
                for sys in test_systems[:random.randint(3, 5)]:
                    self.create_asset(sys, "Equipment", env["id"])
    
    def _create_aircraft_systems(self, parent_id):
        """Create aircraft technical systems"""
        # For each E-3A aircraft
        aircraft_ids = [
            "LX-N90442", "LX-N90443", "LX-N90444", "LX-N90445",
            "LX-N90446", "LX-N90447", "LX-N90448", "LX-N90449",
            "LX-N90450", "LX-N90451", "LX-N90452", "LX-N90453",
            "LX-N90454", "LX-N90455"
        ]
        
        # Create detailed systems for first 3 aircraft, simplified for others
        for idx, aircraft_id in enumerate(aircraft_ids):
            aircraft = self.create_asset(f"E-3A {aircraft_id}", "System", parent_id,
                                        f"Boeing E-3A Sentry {aircraft_id}",
                                        {"tail_number": aircraft_id, 
                                         "manufacturer": "Boeing",
                                         "year": str(1982 + idx)})
            if aircraft and idx < 3:  # Detailed for first 3
                self._create_aircraft_subsystems(aircraft["id"], aircraft_id)
            elif aircraft:  # Simplified for others
                # Just add main subsystems
                subsystems = [
                    "Mission System",
                    "Avionics Suite",
                    "Communications Suite",
                    "Navigation System"
                ]
                for subsys in subsystems:
                    self.create_asset(f"{aircraft_id} {subsys}", "Subsystem", aircraft["id"])
    
    def _create_aircraft_subsystems(self, parent_id, aircraft_id):
        """Create detailed aircraft subsystems"""
        # Mission System Suite
        mission = self.create_asset(f"{aircraft_id} Mission Suite", "Subsystem", parent_id)
        if mission:
            mission_components = [
                "Radar System AN/APY-2",
                "IFF System",
                "ESM/ECM Suite",
                "Data Processing System",
                "Display System"
            ]
            for comp in mission_components:
                c = self.create_asset(f"{comp}", "Module", mission["id"])
                if c and random.random() > 0.5:
                    # Add subcomponents
                    for i in range(random.randint(2, 4)):
                        self.create_asset(f"{comp} Unit {i+1}", "Component", c["id"])
        
        # Communications Suite
        comm = self.create_asset(f"{aircraft_id} Comm Suite", "Subsystem", parent_id)
        if comm:
            comm_systems = [
                "HF Communication System",
                "VHF/UHF Radio System",
                "SATCOM System",
                "Intercom System",
                "Data Link Terminal"
            ]
            for sys in comm_systems:
                self.create_asset(sys, "Module", comm["id"])
    
    def _create_support_infrastructure(self, parent_id):
        """Create support infrastructure"""
        # Maintenance Systems
        maint = self.create_asset("Maintenance Management", "Subsystem", parent_id,
                                 "Aircraft maintenance tracking")
        if maint:
            maint_systems = [
                "PMCS Tracking System",
                "Parts Inventory System",
                "Maintenance Scheduling",
                "Technical Documentation",
                "Fault Reporting System"
            ]
            for sys in maint_systems:
                s = self.create_asset(sys, "Application", maint["id"])
                if s:
                    self.create_asset(f"{sys} Database", "Database", s["id"])
        
        # Logistics Support
        log = self.create_asset("Logistics Support", "Subsystem", parent_id,
                               "Supply chain and logistics")
        if log:
            log_systems = [
                "Supply Chain Management",
                "Spare Parts Warehouse",
                "Fuel Management System",
                "Transportation Planning"
            ]
            for sys in log_systems:
                self.create_asset(sys, "Module", log["id"])
        
        # IT Infrastructure
        it = self.create_asset("IT Infrastructure", "Subsystem", parent_id,
                              "Information technology backbone")
        if it:
            self._create_it_infrastructure(it["id"])
    
    def _create_it_infrastructure(self, parent_id):
        """Create IT infrastructure components"""
        # Network Infrastructure
        net = self.create_asset("Network Infrastructure", "Network", parent_id)
        if net:
            network_components = [
                "Core Router Cluster",
                "Distribution Switches",
                "Firewall Cluster",
                "Load Balancers",
                "VPN Gateways",
                "DMZ Infrastructure"
            ]
            for comp in network_components:
                c = self.create_asset(comp, "Equipment", net["id"])
                if c and random.random() > 0.5:
                    # Add redundant units
                    for i in range(2):
                        self.create_asset(f"{comp} Unit {i+1}", "Component", c["id"])
        
        # Data Centers
        dc = self.create_asset("Data Centers", "Facility", parent_id)
        if dc:
            datacenters = [
                ("Primary Data Center", "Main processing facility"),
                ("Backup Data Center", "Disaster recovery site"),
                ("Edge Computing Nodes", "Distributed processing")
            ]
            for dc_name, desc in datacenters:
                datacenter = self.create_asset(dc_name, "Facility", dc["id"], desc)
                if datacenter:
                    # Add servers
                    server_types = [
                        "Database Servers",
                        "Application Servers",
                        "Web Servers",
                        "Storage Arrays",
                        "Virtualization Hosts"
                    ]
                    for server_type in server_types[:random.randint(3, 5)]:
                        srv = self.create_asset(server_type, "Equipment", datacenter["id"])
                        if srv:
                            # Add server instances
                            for i in range(random.randint(2, 4)):
                                self.create_asset(f"{server_type} Instance {i+1}", 
                                                "Processor", srv["id"])
        
        # Security Infrastructure
        sec = self.create_asset("Security Infrastructure", "Module", parent_id)
        if sec:
            security_components = [
                "SIEM System",
                "Intrusion Detection System",
                "Vulnerability Scanner",
                "Security Operations Center",
                "Incident Response Platform"
            ]
            for comp in security_components:
                self.create_asset(comp, "Application", sec["id"])
    
    def add_additional_assets_to_reach_target(self, target=1000):
        """Add additional assets to reach target count"""
        print(f"\nCurrent asset count: {self.asset_count}")
        
        if self.asset_count >= target:
            return
        
        print(f"Adding additional assets to reach {target}...")
        
        # Get all created assets that can be parents
        potential_parents = [a for a in self.created_assets 
                           if a and random.random() > 0.3]  # 70% chance to be parent
        
        additional_types = [
            ("Service", ["Authentication Service", "Logging Service", "Monitoring Service",
                        "Backup Service", "Scheduling Service", "Notification Service"]),
            ("Interface", ["REST API", "SOAP Interface", "Message Queue", "Event Bus",
                          "File Transfer", "Data Feed"]),
            ("Component", ["Processing Unit", "Control Module", "Data Handler",
                          "Message Processor", "Event Handler", "Task Scheduler"]),
            ("Module", ["Analysis Module", "Reporting Module", "Integration Module",
                       "Conversion Module", "Validation Module", "Transformation Module"]),
            ("Application", ["Monitoring Tool", "Analysis Tool", "Reporting Tool",
                           "Admin Console", "User Portal", "Dashboard"]),
            ("Database", ["Operational DB", "Historical DB", "Config DB", "Log DB",
                         "Audit DB", "Reference DB"]),
            ("Equipment", ["Server Unit", "Network Device", "Storage Unit",
                          "Backup Device", "Security Appliance", "Communication Device"]),
            ("Sensor", ["Temperature Sensor", "Pressure Sensor", "Status Monitor",
                       "Performance Monitor", "Health Monitor", "Activity Sensor"])
        ]
        
        while self.asset_count < target:
            # Select random parent
            if potential_parents and random.random() > 0.2:  # 80% chance to have parent
                parent = random.choice(potential_parents)
                parent_id = parent["id"]
            else:
                parent_id = None
            
            # Select random type and name
            asset_type, names = random.choice(additional_types)
            name_template = random.choice(names)
            
            # Generate unique name
            suffix = f"_{random.randint(100, 999)}"
            if random.random() > 0.5:
                suffix += f"_{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
            
            name = f"{name_template}{suffix}"
            
            # Create metadata
            metadata = {}
            if random.random() > 0.5:
                metadata["version"] = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,99)}"
            if random.random() > 0.5:
                metadata["location"] = random.choice(["Geilenkirchen", "Remote", "Mobile", "Distributed"])
            if random.random() > 0.5:
                metadata["criticality"] = random.choice(["High", "Medium", "Low"])
            if random.random() > 0.5:
                metadata["vendor"] = random.choice(["Boeing", "Northrop Grumman", "Raytheon", 
                                                   "Lockheed Martin", "General Dynamics", "NATO"])
            
            # Create asset
            asset = self.create_asset(name, asset_type, parent_id, metadata=metadata)
            
            # Add to potential parents if it's a good candidate
            if asset and random.random() > 0.5:
                potential_parents.append(asset)
            
            # Progress indicator
            if self.asset_count % 50 == 0:
                print(f"  Progress: {self.asset_count}/{target} assets created")
        
        print(f"✓ Reached target: {self.asset_count} assets created")
    
    def generate_sample_boms(self):
        """Generate sample BOMs for some assets"""
        print("\nGenerating sample BOMs...")
        
        # Select random assets for BOM generation
        bom_candidates = random.sample(self.created_assets, 
                                      min(50, len(self.created_assets)))
        
        for asset in bom_candidates:
            bom_data = {
                "asset_id": asset["id"],
                "version": f"{random.randint(1,3)}.{random.randint(0,9)}",
                "components": []
            }
            
            # Add random components to BOM
            num_components = random.randint(3, 10)
            for i in range(num_components):
                component = {
                    "name": f"Component_{random.choice(['SW', 'HW', 'FW'])}_{random.randint(1000, 9999)}",
                    "version": f"{random.randint(1,10)}.{random.randint(0,99)}.{random.randint(0,999)}",
                    "type": random.choice(["software", "hardware", "firmware"]),
                    "vendor": random.choice(["Boeing", "Northrop Grumman", "Raytheon", 
                                           "Microsoft", "Oracle", "RedHat", "NATO"]),
                    "license": random.choice(["Proprietary", "GPL", "MIT", "Apache 2.0", 
                                            "Commercial", "NATO Use Only"])
                }
                bom_data["components"].append(component)
            
            # Upload BOM
            response = requests.post(f"{API_BASE}/assets/{asset['id']}/bom", 
                                    json=bom_data)
            if response.status_code == 200:
                print(f"  ✓ Added BOM to {asset['name']}")

def main():
    print("=" * 60)
    print("NATO AWACS Test Data Population Script")
    print("=" * 60)
    
    generator = NATOAWACSDataGenerator()
    
    # Create asset types
    generator.create_asset_types()
    
    # Generate main hierarchy
    generator.generate_nato_awacs_hierarchy()
    
    # Add additional assets to reach 1000
    generator.add_additional_assets_to_reach_target(1000)
    
    # Generate some BOMs
    generator.generate_sample_boms()
    
    print("\n" + "=" * 60)
    print(f"✓ Data population complete!")
    print(f"  Total assets created: {generator.asset_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()