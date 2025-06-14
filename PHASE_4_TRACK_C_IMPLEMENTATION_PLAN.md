# Phase 4 Track C: API-First Web Interface Implementation Plan

## Project Overview

**Goal**: Create specialized API endpoints for external applications to interact with philosophical assistants using predefined templates, enabling structured philosophical reasoning and analysis.

**Timeline**: 4 weeks
**Priority**: High - Foundation for external integrations

## 1. Endpoint Requirements

### 1.1 Core Template Endpoints

#### A. Resolve Endpoint

```
POST /api/v1/assistants/{assistant_id}/resolve
```

**Purpose**: Correct philosophical misconceptions from the assistant's worldview perspective

**Templates Used**:

-   `gedankenfehler-formulieren.mdt` (main)
-   `gedankenfehler-formulieren-aspekte.mdt` (optional aspects)

**Input**:

```json
{
    "gedanke_in_weltanschauung": "Thinking mistake to correct (max 500 chars)",
    "aspekte": "Optional specific aspects to consider (max 200 chars)"
}
```

**Output**:

```json
{
    "gedanke": "300-word philosophical correction",
    "gedanke_zusammenfassung": "Brief summary of correction",
    "gedanke_kind": "Child-friendly explanation (10-year-old level)",
    "assistant_id": "string",
    "weltanschauung": "string",
    "processing_time": "number"
}
```

#### B. Reformulate Endpoint

```
POST /api/v1/assistants/{assistant_id}/reformulate
```

**Purpose**: Reformulate a thought from the assistant's worldview perspective

**Templates Used**:

-   `gedankenfehler-wiederholen.mdt`

**Input**:

```json
{
    "gedanke": "Original thought to reformulate (max 200 chars)",
    "stichwort": "Comma-separated keywords to incorporate (max 100 chars)"
}
```

**Output**:

```json
{
    "gedanken_in_weltanschauung": [
        "Array of 3 reformulated variations (max 20 words each)"
    ],
    "gedanke": "Original thought (echoed back)",
    "assistant_id": "string",
    "weltanschauung": "string",
    "processing_time": "number"
}
```

#### C. Glossary Endpoint

```
POST /api/v1/assistants/{assistant_id}/glossary
```

**Purpose**: Generate philosophical glossary from text or concepts

**Templates Used**:

-   `gedankenfehler-glossar.mdt`

**Input** (either text OR concepts):

```json
{
    "korrektur": "Text to extract concepts from (max 1000 chars)",
    // OR
    "begriffe": ["Array of specific concepts to define (max 5)"]
}
```

**Output**:

```json
{
    "glossar": [
        {
            "begriff": "Philosophical concept",
            "beschreibung": "50-80 word explanation from worldview perspective"
        }
    ],
    "assistant_id": "string",
    "weltanschauung": "string",
    "processing_time": "number"
}
```

### 1.2 Assistant Management Endpoint

#### D. List Assistants Endpoint

```
GET /api/v1/assistants
```

**Purpose**: List available philosophical assistants for external applications

**Query Parameters**:

-   `weltanschauung` (optional): Filter by specific worldview
-   `status` (optional): Filter by assistant status
-   `include_capabilities` (optional): Include template capabilities in response

**Output**:

```json
{
    "assistants": [
        {
            "id": "string",
            "name": "string",
            "weltanschauung": "Idealismus|Materialismus|Realismus|Spiritualismus",
            "model": "deepseek-reasoner",
            "status": "Ready|Initializing|Failed",
            "description": "string",
            "created_at": "datetime",
            "capabilities": {
                "templates": ["resolve", "reformulate", "glossary"],
                "max_context_length": "number",
                "supported_languages": ["de", "en"]
            }
        }
    ],
    "total_count": "number",
    "available_worldviews": [
        "Idealismus",
        "Materialismus",
        "Realismus",
        "Spiritualismus"
    ]
}
```

## 2. Implementation Architecture

### 2.1 File Structure

```
app/
├── api/v1/assistants/
│   ├── __init__.py
│   ├── routes.py                    # Existing assistant routes
│   ├── template_routes.py           # New template-based routes
│   ├── schemas.py                   # Request/response schemas
│   └── template_processor.py       # Template processing logic

assistants/
├── templates/                       # Existing .mdt files
│   ├── gedankenfehler-formulieren.mdt
│   ├── gedankenfehler-formulieren-aspekte.mdt
│   ├── gedankenfehler-wiederholen.mdt
│   └── gedankenfehler-glossar.mdt
├── template_engine.py               # New template engine
└── pinecone_assistant_manager.py   # Enhanced with template support
```

### 2.2 Core Components

#### A. Template Engine

```python
class TemplateEngine:
    def load_template(self, template_name: str) -> str
    def render_template(self, template: str, variables: Dict) -> str
    def validate_template_response(self, response: str, expected_schema: Dict) -> Dict
    def extract_json_from_response(self, response: str) -> Dict
    def handle_malformed_json(self, response: str) -> Dict
```

#### B. Assistant Template Processor

```python
class AssistantTemplateProcessor:
    def __init__(self, assistant_manager: PineconeAssistantManager, template_engine: TemplateEngine)

    def process_resolve_request(self, assistant_id: str, request: ResolveRequest) -> ResolveResponse
    def process_reformulate_request(self, assistant_id: str, request: ReformulateRequest) -> ReformulateResponse
    def process_glossary_request(self, assistant_id: str, request: GlossaryRequest) -> GlossaryResponse
    def list_assistants_with_capabilities(self, filters: Dict) -> AssistantListResponse
```

#### C. Enhanced Assistant Manager

```python
# Extensions to existing PineconeAssistantManager
class PineconeAssistantManager:
    # New methods
    def query_with_template(self, assistant_id: str, template: str, variables: Dict) -> Dict
    def validate_assistant_response(self, response: str, expected_format: str) -> bool
    def get_assistant_capabilities(self, assistant_id: str) -> Dict
    def list_assistants_extended(self, include_capabilities: bool = False) -> List[Dict]
```

## 3. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Template Engine Development

-   **Day 1-2**: Create `TemplateEngine` class

    -   Load `.mdt` files from templates directory
    -   Implement `{{ variable }}` substitution
    -   Add template validation
    -   Error handling for missing templates

-   **Day 3-4**: JSON Response Processing

    -   Parse JSON from assistant responses
    -   Handle malformed JSON gracefully
    -   Implement fallback mechanisms
    -   Add response validation against schemas

-   **Day 5**: Testing & Documentation
    -   Unit tests for template engine
    -   Template loading performance tests
    -   Documentation for template format

#### 1.2 Enhanced Assistant Manager

-   **Day 1-2**: Extend `PineconeAssistantManager`

    -   Add `query_with_template()` method
    -   Implement response validation
    -   Add capability detection

-   **Day 3-4**: Assistant Listing Enhancement

    -   Extend `list_assistants()` with filtering
    -   Add capability information
    -   Implement status checking

-   **Day 5**: Integration Testing
    -   Test template integration with assistant manager
    -   Validate worldview consistency
    -   Performance benchmarking

### Phase 2: API Endpoint Implementation (Week 2)

#### 2.1 Schema Definition

-   **Day 1**: Create Pydantic Models
    -   Request schemas for all three endpoints
    -   Response schemas with validation rules
    -   Error response schemas
    -   Assistant listing schemas

#### 2.2 Template Routes Development

-   **Day 2-3**: Implement Template Endpoints

    -   Create `template_routes.py`
    -   Implement resolve endpoint
    -   Implement reformulate endpoint
    -   Implement glossary endpoint

-   **Day 4**: Assistant Listing Endpoint

    -   Enhance existing `/assistants` endpoint
    -   Add filtering and capability information
    -   Implement query parameter handling

-   **Day 5**: Error Handling & Validation
    -   Comprehensive input validation
    -   Error response formatting
    -   Rate limiting considerations

#### 2.3 Integration Testing

-   **Day 6-7**: End-to-End Testing
    -   Test all endpoints with real assistants
    -   Validate JSON response formats
    -   Test error scenarios
    -   Performance testing

### Phase 3: OpenAPI Enhancement & Documentation (Week 3)

#### 3.1 OpenAPI Specification Update

-   **Day 1-2**: Update `personal-rag-server-openapi.yaml`
    -   Add four new endpoint definitions
    -   Complete request/response schema documentation
    -   Add comprehensive examples
    -   Include error response documentation

#### 3.2 API Documentation

-   **Day 3-4**: Create Usage Documentation
    -   API usage examples for each endpoint
    -   Template format documentation
    -   Integration guides for external applications
    -   Best practices and limitations

#### 3.3 Testing with OpenAPI

-   **Day 5**: Validation & Testing
    -   Validate OpenAPI specification
    -   Generate test client from spec
    -   Test all documented examples
    -   Ensure schema compliance

### Phase 4: Production Readiness (Week 4)

#### 4.1 Security & Performance

-   **Day 1-2**: Security Implementation
    -   Rate limiting for template endpoints
    -   Input sanitization and size limits
    -   Authentication/authorization integration
    -   Request logging and monitoring

#### 4.2 Performance Optimization

-   **Day 3-4**: Performance Enhancements
    -   Template caching mechanism
    -   Response time monitoring
    -   Database query optimization
    -   Load testing and tuning

#### 4.3 Monitoring & Production

-   **Day 5**: Production Deployment
    -   Structured logging implementation
    -   Performance metrics collection
    -   Error tracking and alerting
    -   Deployment verification

## 4. Technical Specifications

### 4.1 Template Processing Pipeline

1. **Request Validation**: Validate input against Pydantic schemas
2. **Template Loading**: Load appropriate `.mdt` template
3. **Variable Substitution**: Replace `{{ variables }}` with request data
4. **Assistant Query**: Send formatted prompt to philosophical assistant
5. **Response Parsing**: Extract JSON from assistant response
6. **Validation**: Validate response against expected schema
7. **Error Handling**: Handle malformed responses gracefully
8. **Response Formation**: Return formatted API response

### 4.2 Error Handling Strategy

-   **Input Validation Errors**: Return 400 with detailed field errors
-   **Assistant Not Found**: Return 404 with assistant availability info
-   **Template Processing Errors**: Return 500 with fallback responses
-   **Malformed JSON**: Attempt parsing recovery, return partial results
-   **Timeout Errors**: Return 408 with retry suggestions
-   **Rate Limiting**: Return 429 with retry-after headers

### 4.3 Performance Requirements

-   **Response Time**: < 10 seconds for template processing
-   **Throughput**: 100+ concurrent requests
-   **Availability**: 99.9% uptime
-   **Success Rate**: > 95% successful responses
-   **Template Cache**: < 100ms template loading

### 4.4 Security Considerations

-   **Input Sanitization**: XSS prevention, SQL injection protection
-   **Rate Limiting**: 60 requests/minute per user
-   **Authentication**: JWT tokens or API keys required
-   **Authorization**: Role-based access to different assistants
-   **Logging**: All requests logged for audit purposes

## 5. Testing Strategy

### 5.1 Unit Tests

-   Template engine functionality
-   Schema validation
-   Assistant manager extensions
-   Error handling scenarios

### 5.2 Integration Tests

-   End-to-end template processing
-   Assistant response validation
-   API endpoint functionality
-   Authentication and authorization

### 5.3 Performance Tests

-   Load testing with multiple concurrent users
-   Template caching effectiveness
-   Database query performance
-   Response time under load

### 5.4 Quality Assurance

-   Manual testing of philosophical response quality
-   Worldview consistency validation
-   Template format compliance
-   Documentation accuracy

## 6. Success Metrics

### 6.1 Functional Success

-   ✅ All four endpoints operational
-   ✅ JSON responses match schemas 100%
-   ✅ Template processing success rate > 95%
-   ✅ Comprehensive error handling

### 6.2 Performance Success

-   ✅ Average response time < 5 seconds
-   ✅ 99.9% uptime
-   ✅ Handle 100+ concurrent requests
-   ✅ Template cache hit rate > 90%

### 6.3 Quality Success

-   ✅ Philosophical response accuracy validated
-   ✅ Complete API documentation
-   ✅ All tests passing
-   ✅ External application integration successful

## 7. Risk Mitigation

### 7.1 Technical Risks

-   **Assistant API Changes**: Abstract interactions, use adapters
-   **Template Format Changes**: Version template schemas
-   **Performance Issues**: Implement caching, timeouts, queuing
-   **JSON Parsing Failures**: Robust error handling, fallbacks

### 7.2 Integration Risks

-   **External Dependencies**: Minimize dependencies, add health checks
-   **Schema Evolution**: Design backward-compatible APIs
-   **Deployment Issues**: Staged rollout, rollback procedures

## 8. Future Enhancements

### 8.1 Phase 5 Considerations

-   **Multi-Assistant Templates**: Templates using multiple worldviews
-   **Custom Template Upload**: Allow users to define custom templates
-   **Real-time Features**: WebSocket support for streaming responses
-   **Analytics Dashboard**: Usage metrics and response quality tracking

### 8.2 Scalability Roadmap

-   **Horizontal Scaling**: Container orchestration support
-   **Caching Strategy**: Redis integration for distributed caching
-   **Queue System**: Background processing for complex templates
-   **CDN Integration**: Static asset delivery optimization

---

**Implementation Ready**: This plan provides a complete roadmap for Phase 4 Track C, creating a robust API foundation for external philosophical assistant integrations. 🚀
