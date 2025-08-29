"""Demonstration script for the advanced real-world task templates."""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from manager.core.schemas import TaskSpec
from manager.core.manager import ManagerCore


async def create_template_tasks():
    """Create sample tasks from each advanced template to showcase capabilities."""
    
    print("AI Manager Advanced Templates Demo")
    print("=" * 60)
    
    manager = ManagerCore()
    
    # Advanced template definitions for demonstration
    advanced_templates = [
        {
            "template_id": "ml-pipeline",
            "title": "Customer Churn Prediction Pipeline",
            "goal": "Build ML pipeline to predict customer churn with 90%+ accuracy",
            "background": "E-commerce platform needs to identify customers likely to churn within 30 days",
        },
        {
            "template_id": "microservice-ecosystem", 
            "title": "Order Management Microservices",
            "goal": "Create scalable microservice architecture for order processing",
            "background": "High-traffic e-commerce site needs to handle 10k+ orders per minute",
        },
        {
            "template_id": "react-dashboard",
            "title": "Real-Time Analytics Dashboard",
            "goal": "Build responsive dashboard for monitoring business metrics",
            "background": "Executive team needs live visibility into KPIs and performance metrics",
        },
        {
            "template_id": "blockchain-dapp",
            "title": "NFT Marketplace DApp",
            "goal": "Develop decentralized marketplace for NFT trading",
            "background": "Artists need platform to mint, sell, and trade digital artwork as NFTs",
        },
        {
            "template_id": "data-warehouse",
            "title": "Multi-Source Analytics Warehouse", 
            "goal": "Build ETL pipeline aggregating data from 10+ sources",
            "background": "Company has siloed data in CRM, ERP, marketing tools needing unification",
        },
        {
            "template_id": "mobile-app-backend",
            "title": "Social Media App Backend",
            "goal": "Create scalable backend supporting 100k+ concurrent users",
            "background": "New social platform needs robust API with real-time features",
        },
        {
            "template_id": "iot-platform",
            "title": "Smart Factory IoT Platform",
            "goal": "Build platform monitoring 1000+ industrial sensors",
            "background": "Manufacturing facility needs real-time monitoring and predictive maintenance",
        },
        {
            "template_id": "e-commerce-platform",
            "title": "Multi-Vendor Marketplace",
            "goal": "Develop complete marketplace supporting multiple sellers",
            "background": "Business needs platform rivaling Amazon with vendor management",
        },
        {
            "template_id": "devops-infrastructure",
            "title": "Cloud-Native DevOps Platform",
            "goal": "Set up complete CI/CD infrastructure on Kubernetes",
            "background": "Development team of 50+ engineers needs automated deployment pipeline",
        },
        {
            "template_id": "ai-chatbot",
            "title": "Customer Service AI Assistant",
            "goal": "Build intelligent chatbot handling 80% of support requests",
            "background": "Support team overwhelmed with 1000+ daily tickets needing automation",
        }
    ]
    
    created_tasks = []
    
    for template_config in advanced_templates:
        print(f"\nCreating: {template_config['title']}")
        print(f"   Template: {template_config['template_id']}")
        print(f"   Goal: {template_config['goal']}")
        
        try:
            # Create task spec from template
            import datetime, uuid
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            task_id = f"{template_config['template_id'].upper()}-DEMO-{timestamp}-{str(uuid.uuid4())[:8]}"
            
            # Get template configuration (this would normally come from the API)
            template_configs = get_template_configs()
            template = template_configs.get(template_config['template_id'])
            
            if not template:
                print(f"   ERROR: Template {template_config['template_id']} not found")
                continue
            
            task_spec = TaskSpec(
                task_id=task_id,
                title=template_config['title'],
                goal=template_config['goal'], 
                background=template_config['background'],
                deliverables=template['deliverables'],
                definition_of_done=template['definition_of_done'],
                timebox_hours=template['timebox_hours']
            )
            
            # Submit task
            created_task_id = await manager.submit_task(task_spec)
            created_tasks.append({
                "task_id": created_task_id,
                "title": template_config['title'],
                "template": template_config['template_id'],
                "complexity": template.get('complexity', 'high'),
                "timebox_hours": template['timebox_hours'],
                "deliverable_count": len(template['deliverables'])
            })
            
            print(f"   SUCCESS: Created {created_task_id}")
            print(f"      Deliverables: {len(template['deliverables'])}")
            print(f"      Time Budget: {template['timebox_hours']} hours")
            
        except Exception as e:
            print(f"   ERROR: {e}")
    
    return created_tasks


def get_template_configs() -> Dict:
    """Get template configurations (matches the API implementation)."""
    return {
        "ml-pipeline": {
            "deliverables": ["Data preprocessing modules", "Model training scripts", "Model evaluation metrics", "FastAPI inference service", "Docker containerization", "CI/CD pipeline config", "Model versioning system", "Comprehensive test suite", "Documentation and examples"],
            "definition_of_done": ["Pipeline runs end-to-end", "Model metrics acceptable", "API inference working", "Docker builds successfully", "Tests pass with >85% coverage", "Documentation complete"],
            "timebox_hours": 8.0,
            "complexity": "high"
        },
        "microservice-ecosystem": {
            "deliverables": ["API Gateway service", "User management service", "Data service with database", "Message queue integration", "Service discovery setup", "Docker Compose orchestration", "Health check endpoints", "Load testing scripts", "Monitoring and logging", "API documentation"],
            "definition_of_done": ["All services start successfully", "Inter-service communication works", "Load tests pass", "Health checks responsive", "Monitoring dashboards functional", "API docs complete"],
            "timebox_hours": 12.0,
            "complexity": "high"
        },
        "react-dashboard": {
            "deliverables": ["React application structure", "Component library", "Chart.js integrations", "WebSocket client", "State management (Redux)", "Responsive CSS/Styled Components", "Unit tests with Jest", "Storybook documentation", "Build and deployment scripts"],
            "definition_of_done": ["Application builds successfully", "All components render properly", "Charts display data correctly", "WebSocket connections work", "Tests pass >90% coverage", "Responsive on all devices"],
            "timebox_hours": 10.0,
            "complexity": "high"
        },
        "blockchain-dapp": {
            "deliverables": ["Solidity smart contracts", "Contract deployment scripts", "Web3.js frontend integration", "MetaMask connectivity", "Event listening system", "Security audit checklist", "Gas optimization analysis", "Unit tests for contracts", "Frontend UI components"],
            "definition_of_done": ["Contracts deploy successfully", "Frontend connects to blockchain", "MetaMask integration works", "Events are captured properly", "Security audit passed", "Gas usage optimized"],
            "timebox_hours": 15.0,
            "complexity": "high"
        },
        "data-warehouse": {
            "deliverables": ["Data extraction modules", "Transformation pipelines", "Data quality checks", "Database schema design", "Apache Airflow DAGs", "Data validation tests", "Performance monitoring", "Analytics SQL queries", "Reporting dashboards"],
            "definition_of_done": ["ETL pipeline runs successfully", "Data quality checks pass", "Airflow DAGs scheduled", "Performance acceptable", "Dashboards render data", "SQL queries optimized"],
            "timebox_hours": 12.0,
            "complexity": "high"
        },
        "mobile-app-backend": {
            "deliverables": ["REST API endpoints", "JWT authentication system", "Push notification service", "File upload handling", "Database models and migrations", "API rate limiting", "Caching layer (Redis)", "API documentation", "Load testing suite"],
            "definition_of_done": ["All endpoints functional", "Authentication secure", "Push notifications work", "File uploads handle all types", "Database performance good", "Rate limiting effective", "Load tests pass"],
            "timebox_hours": 8.0,
            "complexity": "high"
        },
        "iot-platform": {
            "deliverables": ["MQTT broker setup", "Device data ingestion", "Time-series database", "Real-time stream processing", "Device management API", "Alert system", "Data visualization dashboard", "Device simulation tools", "Scaling documentation"],
            "definition_of_done": ["MQTT broker operational", "Data ingestion reliable", "Stream processing responsive", "Device management functional", "Alerts trigger correctly", "Dashboard shows live data", "Simulation tools work"],
            "timebox_hours": 14.0,
            "complexity": "high"
        },
        "e-commerce-platform": {
            "deliverables": ["Product catalog API", "Shopping cart system", "Payment gateway integration", "Inventory management", "Order processing workflow", "User authentication", "Admin dashboard", "Email notification system", "Search and filtering"],
            "definition_of_done": ["Product catalog browsable", "Cart operations work", "Payments process successfully", "Inventory tracks accurately", "Order workflow complete", "User auth secure", "Admin functions operational"],
            "timebox_hours": 16.0,
            "complexity": "high"
        },
        "devops-infrastructure": {
            "deliverables": ["Terraform infrastructure code", "GitHub Actions workflows", "Docker multi-stage builds", "Kubernetes deployments", "Prometheus monitoring", "Grafana dashboards", "Log aggregation (ELK)", "Security scanning", "Backup and recovery"],
            "definition_of_done": ["Infrastructure provisions", "CI/CD pipeline functional", "Docker builds optimized", "K8s deployments stable", "Monitoring captures metrics", "Dashboards show data", "Security scans pass"],
            "timebox_hours": 12.0,
            "complexity": "high"
        },
        "ai-chatbot": {
            "deliverables": ["NLP processing pipeline", "Intent recognition system", "Conversation flow engine", "Knowledge base integration", "Learning and feedback system", "Multi-platform deployment", "Analytics dashboard", "Training data management", "Performance optimization"],
            "definition_of_done": ["NLP pipeline processes text", "Intent recognition accurate", "Conversations flow naturally", "Knowledge base accessible", "Learning improves responses", "Deploys to all platforms", "Analytics track usage"],
            "timebox_hours": 10.0,
            "complexity": "high"
        }
    }


def display_template_showcase():
    """Display information about all available templates."""
    
    print("\nADVANCED TEMPLATE SHOWCASE")
    print("=" * 60)
    
    template_configs = get_template_configs()
    
    categories = {
        "Machine Learning": ["ml-pipeline"],
        "Architecture & Backend": ["microservice-ecosystem", "mobile-app-backend", "iot-platform"],
        "Frontend & UI": ["react-dashboard"],
        "Blockchain & Web3": ["blockchain-dapp"], 
        "Data Engineering": ["data-warehouse"],
        "E-Commerce": ["e-commerce-platform"],
        "DevOps & Infrastructure": ["devops-infrastructure"],
        "AI & Automation": ["ai-chatbot"]
    }
    
    total_deliverables = 0
    total_hours = 0
    
    for category, template_ids in categories.items():
        print(f"\n{category}")
        print("-" * 40)
        
        for template_id in template_ids:
            template = template_configs.get(template_id, {})
            deliverables_count = len(template.get('deliverables', []))
            hours = template.get('timebox_hours', 0)
            
            total_deliverables += deliverables_count
            total_hours += hours
            
            print(f"   {template_id.replace('-', ' ').title()}")
            print(f"      Deliverables: {deliverables_count}")
            print(f"      Hours: {hours}")
            print(f"      Complexity: High")
    
    print(f"\nSUMMARY STATISTICS")
    print("=" * 60)
    print(f"   Total Templates: {len(template_configs)}")
    print(f"   Total Deliverables: {total_deliverables}")
    print(f"   Total Time Budget: {total_hours} hours")
    print(f"   Average per Template: {total_deliverables/len(template_configs):.1f} deliverables")
    print(f"   Average Complexity: High (Advanced Templates)")


async def main():
    """Main demonstration function."""
    
    print("AI Manager: Advanced Real-World Templates Demo")
    print("=" * 80)
    
    # Show template showcase first
    display_template_showcase()
    
    print(f"\n\nCREATING DEMONSTRATION TASKS")
    print("=" * 80)
    
    # Create sample tasks
    try:
        created_tasks = await create_template_tasks()
    except Exception as e:
        print(f"ERROR creating tasks: {e}")
        created_tasks = []
    
    print(f"\nTASK CREATION SUMMARY")
    print("=" * 60)
    print(f"   Successfully Created: {len(created_tasks)} tasks")
    
    if created_tasks:
        total_deliverables = sum(task['deliverable_count'] for task in created_tasks)
        total_hours = sum(task['timebox_hours'] for task in created_tasks)
        
        print(f"   Total Deliverables: {total_deliverables}")
        print(f"   Total Time Budget: {total_hours} hours")
        print(f"   All High Complexity Tasks")
        
        # Show created tasks
        print(f"\nCREATED TASKS:")
        for task in created_tasks:
            print(f"   • {task['task_id']}")
            print(f"     Title: {task['title']}")
            print(f"     Template: {task['template']}")
            print(f"     Deliverables: {task['deliverable_count']}")
            print(f"     Budget: {task['timebox_hours']} hours")
            print()
    
    print(f"\nHOW TO USE THESE TEMPLATES:")
    print("=" * 60)
    print(f"   1. Start API server: python -m cli.api_cli --dev")
    print(f"   2. List templates: curl http://localhost:8000/tasks/templates")
    print(f"   3. Create from template: curl -X POST http://localhost:8000/tasks/from-template/ml-pipeline \\")
    print(f"      -H 'Content-Type: application/json' \\")
    print(f"      -d '{{\"title\": \"My ML Project\", \"goal\": \"Build ML pipeline\"}}'")
    print(f"   4. Monitor dashboard: http://localhost:8000/dashboard")
    
    print(f"\nADVANCED FEATURES DEMONSTRATED:")
    print("=" * 60)
    print(f"   * 10 Industry-Standard Templates")
    print(f"   * Multi-File Project Generation")
    print(f"   * Complex Deliverable Management") 
    print(f"   * Professional Definition-of-Done")
    print(f"   * Real-World Time Estimates")
    print(f"   * Enterprise-Level Complexity")
    print(f"   * AI-Powered Code Generation")
    print(f"   * Comprehensive Testing Support")
    
    print(f"\nREADY FOR PRODUCTION!")
    print("The AI Manager now supports enterprise-level task templates!")


if __name__ == "__main__":
    asyncio.run(main())