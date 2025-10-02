# Python Codebase Evaluation Guide

## Executive Summary

This document provides a comprehensive framework for evaluating Python codebases against modern software development standards. Each criterion includes rationale, evaluation methods, and practical examples to guide assessment.

---

## 1. Clean Code Principles

### 1.1 Readability and Clarity

**What to Look For:**

- Self-documenting code with meaningful names
- Consistent naming conventions (PEP 8 compliance)
- Appropriate abstraction levels
- Clear separation of concerns

**Red Flags:**

```python
# Poor: Unclear naming and purpose
def calc(x, y, z):
    return x * 0.1 + y * 0.2 if z else x * 0.15

# Good: Clear intent and naming
def calculate_discount_price(base_price, loyalty_points, is_member):
    MEMBER_DISCOUNT = 0.1
    LOYALTY_DISCOUNT_RATE = 0.2
    NON_MEMBER_DISCOUNT = 0.15

    if is_member:
        return base_price * MEMBER_DISCOUNT + loyalty_points * LOYALTY_DISCOUNT_RATE
    return base_price * NON_MEMBER_DISCOUNT
```

### 1.2 Single Responsibility Principle

**What to Look For:**

- Classes and functions with one clear purpose
- Minimal side effects
- Cohesive modules

**Example:**

```python
# Poor: Multiple responsibilities
class UserManager:
    def create_user(self, data):
        # Validation logic
        # Database operations
        # Email sending
        # Logging
        pass

# Good: Separated concerns
class UserValidator:
    def validate(self, data): pass

class UserRepository:
    def save(self, user): pass

class EmailService:
    def send_welcome_email(self, user): pass

class UserCreationService:
    def __init__(self, validator, repository, email_service):
        self.validator = validator
        self.repository = repository
        self.email_service = email_service

    def create_user(self, data):
        validated_data = self.validator.validate(data)
        user = self.repository.save(validated_data)
        self.email_service.send_welcome_email(user)
        return user
```

### 1.3 DRY (Don't Repeat Yourself)

**What to Look For:**

- Reusable components and utilities
- Appropriate use of inheritance and composition
- Centralised configuration and constants

### 1.4 Magic Values and Constants Management

**What to Look For:**

- Named constants instead of magic numbers
- Centralised string literals and enums
- Configuration values extracted from code
- Domain-specific constants clearly defined

**Magic Numbers - Red Flags:**

```python
# Poor: Magic numbers with unclear meaning
def calculate_shipping_cost(weight, distance):
    if weight > 50:  # What does 50 represent?
        return distance * 0.75  # What is 0.75?
    elif weight > 20:  # Another magic number
        return distance * 0.5
    else:
        return distance * 0.25  # Unclear rate

# Good: Clear, named constants
from enum import Enum

# Weight thresholds in kilograms
HEAVY_PACKAGE_THRESHOLD_KG = 50
MEDIUM_PACKAGE_THRESHOLD_KG = 20

# Shipping rates per km
HEAVY_PACKAGE_RATE = 0.75
MEDIUM_PACKAGE_RATE = 0.5
LIGHT_PACKAGE_RATE = 0.25

def calculate_shipping_cost(weight: float, distance: float) -> float:
    if weight > HEAVY_PACKAGE_THRESHOLD_KG:
        return distance * HEAVY_PACKAGE_RATE
    elif weight > MEDIUM_PACKAGE_THRESHOLD_KG:
        return distance * MEDIUM_PACKAGE_RATE
    else:
        return distance * LIGHT_PACKAGE_RATE
```

**Magic Strings - Best Practice:**

```python
# Good: Centralised string constants and enums
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class EmailTemplates:
    ORDER_PROCESSING = "Your order is being processed"
    ORDER_SHIPPED = "Your order has been shipped"
    ORDER_DELIVERED = "Your order has been delivered"
```

---

## 2. Testability and Testing Strategy

### 2.1 Test Structure and Coverage

**What to Look For:**

- Tests organised by behaviour, not implementation
- Clear test naming conventions
- Appropriate use of fixtures and mocks
- Test coverage metrics (aim for >80% for critical paths)

### 2.2 Behavioural Testing vs Unit Testing

**Behavioural Testing Example:**

```python
# Poor: Testing implementation details
def test_user_dict_has_email_key():
    user = User("test@example.com")
    assert "email" in user.__dict__

# Good: Testing behaviour
def test_user_can_be_authenticated_with_valid_credentials():
    # Given
    user = User(email="test@example.com", password="secure123")
    auth_service = AuthenticationService()

    # When
    result = auth_service.authenticate("test@example.com", "secure123")

    # Then
    assert result.is_successful
    assert result.user.email == "test@example.com"
```

### 2.3 Test Pyramid Structure

**Ideal Distribution:**

- Unit Tests: 70% - Fast, isolated, numerous
- Integration Tests: 20% - Test component interactions
- End-to-End Tests: 10% - Critical user journeys

---

## 3. Integration Testing

### 3.1 Database Integration Tests

**What to Look For:**

- Test database isolation
- Transaction rollback strategies
- Realistic test data

**Example:**

```python
# Good: Isolated database testing
class TestUserRepository:
    @pytest.fixture
    def db_session(self):
        # Create test database session
        session = create_test_session()
        yield session
        session.rollback()
        session.close()

    def test_user_persistence(self, db_session):
        repo = UserRepository(db_session)
        user = User(email="test@example.com")

        saved_user = repo.save(user)
        retrieved_user = repo.find_by_email("test@example.com")

        assert retrieved_user.id == saved_user.id
```

### 3.2 External Service Integration

**What to Look For:**

- Contract testing
- Service virtualisation/mocking
- Retry and fallback mechanisms

---

## 4. Type Safety and Static Typing

### 4.1 Type Hints Usage

**What to Look For:**

- Comprehensive type annotations
- Use of `typing` module features
- Type checking in CI/CD pipeline

**Example:**

```python
from typing import List, Optional, Dict, Union
from dataclasses import dataclass

@dataclass
class Order:
    id: str
    status: str
    items: List[Dict[str, Union[str, float]]]

def process_orders(
    orders: List[Order],
    filter_status: Optional[str] = None
) -> List[Dict[str, any]]:
    results: List[Dict[str, any]] = []
    for order in orders:
        if not filter_status or order.status == filter_status:
            results.append(order.process())
    return results
```

### 4.2 Runtime Type Checking

**Consider Using:**

- Pydantic for data validation
- dataclasses for structured data
- Protocol classes for structural subtyping

---

## 5. Maintainability

### 5.1 Code Complexity Metrics

**What to Look For:**

- Cyclomatic complexity < 10 per function
- Cognitive complexity considerations
- Function length < 50 lines
- Class length < 300 lines

### 5.2 Documentation

**What to Look For:**

- Comprehensive README
- API documentation
- Inline documentation for complex logic
- Architecture Decision Records (ADRs)

**Good Documentation Example:**

```python
def calculate_compound_interest(
    principal: float,
    rate: float,
    time: int,
    frequency: int = 12
) -> float:
    """
    Calculate compound interest on an investment.

    Args:
        principal: Initial investment amount
        rate: Annual interest rate (as decimal, e.g., 0.05 for 5%)
        time: Investment period in years
        frequency: Compounding frequency per year (default: monthly)

    Returns:
        Total amount after compound interest

    Example:
        >>> calculate_compound_interest(1000, 0.05, 2)
        1104.94
    """
    return principal * (1 + rate/frequency) ** (frequency * time)
```

---

## 6. Configuration Management

### 6.1 Environment-Based Configuration

**What to Look For:**

- Separation of configuration from code
- Environment variable usage
- Secure secrets management

**Example:**

```python
# Good: Centralised configuration
from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    redis_url: str
    api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 6.2 Feature Flags

**What to Look For:**

- Runtime configuration changes
- A/B testing capabilities
- Gradual rollout support

---

## 7. Deployability

### 7.1 Containerisation

**What to Look For:**

- Dockerfile best practices
- Multi-stage builds
- Minimal image sizes

**Example Dockerfile:**

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

### 7.2 CI/CD Pipeline

**What to Look For:**

- Automated testing
- Code quality checks
- Deployment automation
- Rollback capabilities

---

## 8. Additional Modern Practices

### 8.1 Observability

**What to Look For:**

- Structured logging
- Distributed tracing
- Metrics and monitoring
- Error tracking

**Example:**

```python
import logging
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def process_request(request_id: str):
    with tracer.start_as_current_span("process_request") as span:
        span.set_attribute("request.id", request_id)
        logger.info("Processing request", extra={"request_id": request_id})

        try:
            result = perform_operation()
            span.set_status(trace.Status(trace.StatusCode.OK))
            return result
        except Exception as e:
            span.record_exception(e)
            logger.error("Request failed", extra={"request_id": request_id, "error": str(e)})
            raise
```

### 8.2 Security Considerations

**What to Look For:**

- Input validation and sanitisation
- Authentication and authorisation
- Dependency vulnerability scanning
- Secrets management

### 8.3 Performance Optimisation

**What to Look For:**

- Async/await usage where appropriate
- Database query optimisation
- Caching strategies
- Memory management

### 8.4 API Design

**What to Look For:**

- RESTful principles or GraphQL schema design
- Versioning strategy
- Rate limiting
- OpenAPI/Swagger documentation

---

## 9. Clean Code Quick Reference Checklist

### Priority Ranking and Categorisation

#### 🔴 CRITICAL (Must Have)

These practices have the highest impact on code quality and maintainability.

##### **Core Principles**

- Keep It Simple (3)
- Don't Repeat Yourself (26)
- Readability > cleverness (49)
- Readability > efficiency (52)
- Write code for humans to read (83)
- Working ≠ clean code (22)

##### **Naming & Structure**

- Use intention-revealing names (85)
- Names > comments (5)
- Use searchable names (25)
- Use pronounceable names (40)
- Avoid magic numbers (17)
- Avoid magic strings (18)

##### **Function Design**

- Write small functions (28)
- One responsibility/class (57)
- Limit function arguments (50)
- Strive for no side effects in functions (100)
- Max 8-10 lines/function (44)

##### **Testing Fundamentals**

- Test early & often (13)
- Write deterministic tests (59)
- Have one behaviour per test (70)
- Use AAA pattern in tests (48)
- Tests should be as clean as prod code (98)

#### 🟠 HIGH PRIORITY (Should Have)

Essential for professional development but not blocking.

##### **Code Organisation**

- Avoid large classes (20)
- Keep cohesion high (12)
- Strive for low coupling (46)
- Depend on abstractions (39)
- Composition > inheritance (67)
- One responsibility per module (82)

##### **Naming Conventions**

- Use verbs for functions names (84)
- Use nouns for class names (63)
- Prefix your booleans (24)
- Use adjectives for booleans (74)
- Don't use abbreviations (43)
- Use consistent naming (29)

##### **Testing Practices**

- Fakes > mocks (2)
- Write fast tests (7)
- Write repeatable tests (35)
- Write independent tests (42)
- Write self-validating tests (72)
- Use descriptive test names (71)

#### 🟡 MEDIUM PRIORITY (Nice to Have)

Improve code quality but context-dependent.

##### **Comments & Documentation**

- Comments explain why (23)
- Minimize comments (10)
- No extensive comments (30)
- Don't state obvious in comments (89)
- Use comments for API docs (62)

##### **Development Practices**

- Refactor early & often (36)
- Leave code cleaner you found (80)
- Commit early & often (21)
- Do real-time code reviews (64)
- Pair-programming on default (77)

##### **Code Formatting**

- Use auto-formatters (19)
- Keep proper indentation (41)
- Set max line width (15)
- Use formatting standards (55)
- No horizontal alignment (47)

#### 🟢 GOOD PRACTICES (Consider Adopting)

Refinements that polish professional code.

##### **Version Control**

- Link commits to tasks (31)
- Write meaningful commits (58)
- Use present tense in commits (79)
- Use imperative mode in commits (87)

##### **Tool Usage**

- Use solid IDEs (4)
- Master IDE hotkeys (14)
- Use rule of three to remove duplication (99)

### Anti-Pattern Detection Checklist

**Red Flags to Look For:**

- ❌ Functions > 10 lines
- ❌ Classes > 300 lines
- ❌ More than 3 function parameters
- ❌ Boolean parameters in functions
- ❌ Nested conditions > 2 levels
- ❌ Comments explaining what (not why)
- ❌ Duplicated code blocks
- ❌ Hard-to-pronounce names
- ❌ Abbreviations in names
- ❌ Global variables
- ❌ NULL checks everywhere
- ❌ Magic values

---

## Evaluation Scoring Matrix

| Category        | Weight | Key Metrics                                |
| --------------- | ------ | ------------------------------------------ |
| Clean Code      | 20%    | Readability, SRP adherence, DRY principle  |
| Testing         | 25%    | Coverage, test pyramid, behavioural focus  |
| Type Safety     | 10%    | Type hint coverage, runtime validation     |
| Maintainability | 15%    | Complexity metrics, documentation quality  |
| Configuration   | 10%    | Environment separation, secrets management |
| Deployability   | 10%    | Container readiness, CI/CD maturity        |
| Observability   | 5%     | Logging, monitoring, tracing               |
| Security        | 5%     | Vulnerability management, input validation |

---

## Conclusion

A well-architected Python codebase should excel across all these dimensions. Use this guide as a checklist during code reviews, architectural discussions, and when establishing team standards. Remember that whilst perfection is rarely achievable, continuous improvement towards these ideals will result in more robust, maintainable, and scalable applications.

## Further Resources

- PEP 8 - Python Style Guide
- The Twelve-Factor App methodology
- Domain-Driven Design principles
- Test-Driven Development practices
- OWASP Security Guidelines
