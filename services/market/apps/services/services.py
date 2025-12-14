import os
import requests
from typing import Dict, Optional
from .models import Service, Order


class AIService:
    """AI service for generating technical specifications using DeepSeek"""
    
    @staticmethod
    def generate_tz(service_id: str, client_requirements: str) -> str:
        """Generate TZ using DeepSeek API (Free, unlimited requests)"""
        try:
            service = Service.objects.get(id=service_id)
            
            # Build prompt
            template = service.ai_template or "Create a detailed technical specification based on:"
            prompt = f"{template}\n\nClient Requirements:\n{client_requirements}\n\nProvide a structured technical specification in markdown format."
            
            # Call DeepSeek API
            api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-demo')
            
            response = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'system', 
                            'content': 'You are an expert technical specification writer. Create detailed, structured specifications in markdown format with clear sections, deliverables, timeline, and budget.'
                        },
                        {
                            'role': 'user', 
                            'content': prompt
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000,
                    'stream': False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                # Fallback to mock on API error
                return AIService._generate_mock_tz(client_requirements, service.price)
                
        except Service.DoesNotExist:
            raise ValueError("Service not found")
        except requests.exceptions.RequestException:
            # Fallback to mock on network error
            try:
                service = Service.objects.get(id=service_id)
                return AIService._generate_mock_tz(client_requirements, service.price)
            except:
                raise Exception("Failed to generate TZ and fallback failed")
        except Exception as e:
            raise Exception(f"Failed to generate TZ: {str(e)}")
    
    @staticmethod
    def _generate_mock_tz(requirements: str, price: float) -> str:
        """Fallback mock TZ generator (used when DeepSeek API is unavailable)"""
        return f"""# Technical Specification

## Project Overview
{requirements}

## Scope of Work
- **Requirement Analysis**: Detailed review of all requirements and stakeholder needs
- **Design Phase**: UI/UX design, architecture planning, and technology selection
- **Development**: Implementation using modern, scalable technologies
- **Testing**: Comprehensive unit, integration, and acceptance testing
- **Deployment**: Production deployment with monitoring and logging setup

## Deliverables
1. **Source Code**: Clean, well-documented, production-ready codebase
2. **Documentation**: Complete technical and user documentation
3. **Testing Reports**: Comprehensive test coverage reports
4. **Deployment Package**: Containerized application ready for deployment
5. **Training Materials**: User guides and video tutorials

## Technical Stack
- **Frontend**: Modern JavaScript framework (React/Vue/Angular)
- **Backend**: Scalable server architecture (Node.js/Python/Java)
- **Database**: Optimized relational/NoSQL database
- **DevOps**: CI/CD pipeline, Docker, cloud infrastructure

## Project Timeline
- **Phase 1 (Week 1-2)**: Requirements gathering and system design
- **Phase 2 (Week 3-4)**: Core functionality development
- **Phase 3 (Week 5)**: Testing, bug fixes, and optimization
- **Phase 4 (Week 6)**: Deployment, documentation, and handover

**Estimated Duration**: 6 weeks

## Budget
**Total Price**: ${price}

## Payment Terms
- **Milestone 1 (50%)**: Upon project start and design approval
- **Milestone 2 (50%)**: Upon successful delivery and testing

## Additional Terms
- **Revisions**: Up to 2 rounds of revisions included
- **Support**: 30 days post-launch support and bug fixes
- **Maintenance**: Optional monthly maintenance plan available
- **Source Code**: Full ownership transferred upon final payment

---
*This specification is generated based on your requirements. Please review and suggest any modifications before we proceed.*"""


class OrderService:
    """Business logic for orders"""
    
    @staticmethod
    def create_order(service_id: str, client_id: str, agreed_tz: str) -> Order:
        """Create new order"""
        try:
            service = Service.objects.get(id=service_id)
            
            # Check balance via Auth service (simplified for MVP)
            # In production: add JWT token validation and actual balance check
            
            order = Order.objects.create(
                service=service,
                client_id=client_id,
                worker_id=service.owner_id,
                agreed_tz=agreed_tz,
                price=service.price,
                status='pending'
            )
            
            return order
            
        except Service.DoesNotExist:
            raise ValueError("Service not found")
