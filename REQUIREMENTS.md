# UKNF Communication Platform - Project Requirements & Technical Specification

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Technology Stack](#technology-stack)
4. [Architecture Design](#architecture-design)
5. [Detailed Module Requirements](#detailed-module-requirements)
6. [User Interface Requirements](#user-interface-requirements)
7. [Security & Compliance Requirements](#security--compliance-requirements)
8. [Accessibility Requirements (WCAG 2.1 AA)](#accessibility-requirements-wcag-21-aa)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Detailed Implementation Steps](#detailed-implementation-steps)
11. [Testing Strategy](#testing-strategy)
12. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Executive Summary

### Project Vision
Development of an enterprise-grade communication and reporting platform for the Polish Financial Supervision Authority (Urząd Komisji Nadzoru Finansowego - UKNF) to facilitate secure, compliant communication between the regulatory body and supervised financial entities.

### Business Context
UKNF supervises various financial market institutions including banks, insurance companies, investment funds, and pension funds. The platform will enable:
- Secure submission and validation of regulatory reports
- Bidirectional communication on regulatory matters
- Management of official notifications and announcements
- Central repository of regulatory documentation
- Complete audit trail of all interactions

### Key Objectives
- **Security First**: Bank-grade security with multi-layered protection
- **Regulatory Compliance**: Full audit trails, data retention policies, GDPR compliance
- **Enterprise Quality**: High availability (99.9% uptime), scalability, performance
- **Accessibility**: WCAG 2.1 Level AA compliance for inclusive access
- **User Experience**: Intuitive interfaces for both regulated entities and UKNF staff

---

## System Overview

### Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UKNF COMMUNICATION PLATFORM                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
┌───────▼───────┐      ┌───────▼───────┐      ┌────────▼────────┐
│  COMMUNICATION │      │ AUTHENTICATION │      │  ADMINISTRATIVE  │
│     MODULE     │      │  & AUTHORIZAT │      │     MODULE       │
│                │      │  ION MODULE    │      │                  │
└───────────────┘      └────────────────┘      └──────────────────┘
│                       │                        │
├─ Reports         ├─ Authentication        ├─ User Management
├─ Matters         ├─ Access Requests       ├─ Password Policies
├─ Messages        ├─ Authorization         ├─ Roles & Permissions
└─ Library         └─ Contact Forms         └─ Entity Database
                                               └─ Data Updater
```

### User Types

#### External Users (Regulated Entities)
- **Entity Administrators**: Manage organization profile and users
- **Submitters**: Submit reports and documents
- **Authorized Representatives**: Handle official correspondence
- **Read-Only Users**: View submitted materials and responses

#### Internal Users (UKNF Staff)
- **System Administrators**: Full system access and configuration
- **Supervisors**: Review submissions, manage cases
- **Analysts**: Process and validate reports
- **Communication Officers**: Manage announcements and messages
- **Auditors**: Read-only access for audit purposes

---

## Technology Stack

### Frontend Framework: **Next.js 14+ with TypeScript**

#### Rationale
- **Enterprise-Grade Performance**: Server-side rendering (SSR), static site generation (SSG), and incremental static regeneration (ISR)
- **Developer Experience**: Hot module replacement, TypeScript support, API routes
- **SEO & Accessibility**: Built-in optimizations for search engines and accessibility
- **Security**: Built-in CSRF protection, secure headers, XSS protection
- **Scalability**: Edge computing capabilities, CDN optimization
- **Modern React**: React 18+ features including Server Components
- **Polish Ecosystem**: Strong community support in Poland for maintenance

### UI Framework: **shadcn/ui + Tailwind CSS**

#### Rationale
- **Enterprise Quality**: Professional, consistent design system
- **Accessibility**: Components built with Radix UI primitives (WCAG compliant)
- **Customization**: Full control over styling and branding
- **Performance**: Optimized bundle sizes, tree-shaking
- **Maintainability**: Component-based architecture
- **Government-Friendly**: Clean, professional aesthetics appropriate for regulatory bodies

### Backend Framework: **Node.js with NestJS**

#### Rationale
- **Enterprise Architecture**: Built-in support for microservices, modular design
- **TypeScript Native**: Type safety across entire stack
- **Scalability**: Horizontal scaling, microservices support
- **Security**: Guards, interceptors, pipes for validation and authorization
- **Testing**: Built-in testing utilities (unit, integration, e2e)
- **Documentation**: Automatic OpenAPI/Swagger generation
- **Dependency Injection**: Clean, testable code architecture

### Database: **PostgreSQL 15+**

#### Rationale
- **Enterprise Reliability**: ACID compliance, data integrity
- **Performance**: Advanced indexing, query optimization, partitioning
- **Security**: Row-level security, encryption, audit logging
- **Compliance**: GDPR-ready with data retention and deletion policies
- **Complex Queries**: Support for complex financial data analysis
- **JSON Support**: Flexible schema for varying report structures
- **Audit Trail**: Temporal tables and triggers for complete audit history

### Additional Technologies

#### Authentication & Authorization
- **KeyCloak**: Enterprise IAM solution
  - Single Sign-On (SSO)
  - Multi-factor Authentication (MFA)
  - LDAP/AD integration for UKNF internal users
  - OAuth 2.0 / OpenID Connect
  - Fine-grained authorization
  - Session management

#### File Storage
- **MinIO** (S3-compatible object storage)
  - Encryption at rest and in transit
  - Versioning and lifecycle policies
  - High availability and disaster recovery
  - Compliance with data sovereignty requirements

#### Message Queue
- **RabbitMQ** or **Apache Kafka**
  - Asynchronous report processing
  - Event-driven architecture
  - Reliable message delivery
  - Audit event streaming

#### Caching
- **Redis**
  - Session storage
  - API response caching
  - Real-time notifications
  - Rate limiting

#### Search Engine
- **Elasticsearch**
  - Full-text search across documents
  - Advanced filtering and aggregations
  - Audit log analysis

#### Monitoring & Logging
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
  - Centralized logging
  - Real-time monitoring
  - Security event correlation
  - Compliance reporting

#### API Documentation
- **Swagger/OpenAPI 3.0**
  - Interactive API documentation
  - Client SDK generation

#### Version Control & CI/CD
- **GitLab** (on-premise)
  - Source code management
  - CI/CD pipelines
  - Container registry
  - Security scanning

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer (HA)                       │
│                     (NGINX / HAProxy)                            │
└────────────────┬──────────────────────────────┬─────────────────┘
                 │                              │
    ┌────────────▼────────────┐    ┌───────────▼────────────┐
    │   Web Application       │    │   API Gateway           │
    │   (Next.js)             │    │   (NestJS)              │
    │   - SSR/SSG             │    │   - Rate Limiting       │
    │   - Client-side         │    │   - Request Validation  │
    │   - Static Assets       │    │   - JWT Verification    │
    └────────────┬────────────┘    └───────────┬─────────────┘
                 │                              │
                 └───────────┬──────────────────┘
                             │
            ┌────────────────▼───────────────────┐
            │     Authentication Service          │
            │          (KeyCloak)                 │
            │     - SSO / MFA                     │
            │     - User Federation               │
            └────────────────┬───────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼────────┐
│  Communication│   │  Admin         │   │  Notification   │
│  Service      │   │  Service       │   │  Service        │
│  (NestJS)     │   │  (NestJS)      │   │  (NestJS)       │
└───────┬───────┘   └───────┬────────┘   └────────┬────────┘
        │                   │                      │
        └───────────────────┼──────────────────────┘
                            │
        ┌───────────────────┼──────────────────────┐
        │                   │                      │
┌───────▼───────┐  ┌────────▼────────┐   ┌────────▼────────┐
│  PostgreSQL   │  │  MinIO          │   │  Redis          │
│  (Primary +   │  │  (Object        │   │  (Cache &       │
│   Replicas)   │  │   Storage)      │   │   Sessions)     │
└───────────────┘  └─────────────────┘   └─────────────────┘
        │
┌───────▼───────┐  ┌─────────────────┐   ┌─────────────────┐
│  Elasticsearch│  │  RabbitMQ       │   │  Backup         │
│  (Search &    │  │  (Message       │   │  Storage        │
│   Analytics)  │  │   Queue)        │   │  (S3/Tape)      │
└───────────────┘  └─────────────────┘   └─────────────────┘
```

### Security Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      Internet                               │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                 WAF (Web Application Firewall)              │
│                 - DDoS Protection                           │
│                 - SQL Injection Prevention                  │
│                 - XSS Protection                            │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│                  DMZ (Demilitarized Zone)                   │
│  ┌──────────────┐         ┌─────────────────┐              │
│  │ Reverse Proxy│────────▶│ Intrusion       │              │
│  │ (NGINX)      │         │ Detection (IDS) │              │
│  └──────┬───────┘         └─────────────────┘              │
└─────────┼──────────────────────────────────────────────────┘
          │
┌─────────▼──────────────────────────────────────────────────┐
│              Application Security Zone                      │
│  ┌────────────────┐  ┌────────────────┐                    │
│  │ Application    │  │ API Gateway    │                    │
│  │ Servers        │  │ (Auth/Rate     │                    │
│  │                │  │  Limiting)     │                    │
│  └────────┬───────┘  └────────┬───────┘                    │
└───────────┼──────────────────┼────────────────────────────┘
            │                  │
┌───────────▼──────────────────▼────────────────────────────┐
│                  Data Security Zone                        │
│  ┌────────────────┐  ┌────────────────┐                   │
│  │ Database       │  │ File Storage   │                   │
│  │ (Encrypted)    │  │ (Encrypted)    │                   │
│  │ - TDE          │  │ - AES-256      │                   │
│  │ - SSL/TLS      │  │ - Access Log   │                   │
│  └────────────────┘  └────────────────┘                   │
└────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

#### Report Submission Flow
```
┌──────────┐    1. Upload     ┌───────────┐    2. Validate   ┌──────────┐
│ External │─────Report────────▶│   API     │──────Format──────▶│ Validator│
│   User   │                   │  Gateway  │                  │ Service  │
└──────────┘                   └───────────┘                  └────┬─────┘
                                      │                            │
                                      │                            │
                               3. Store Metadata            4. Store File
                                      │                            │
                                      ▼                            ▼
                               ┌───────────┐              ┌──────────────┐
                               │PostgreSQL │              │   MinIO      │
                               │  Database │              │   Storage    │
                               └───────────┘              └──────────────┘
                                      │                            │
                                      └──────────┬─────────────────┘
                                                 │
                                      5. Trigger Processing
                                                 │
                                                 ▼
                                          ┌──────────┐
                                          │ Message  │
                                          │  Queue   │
                                          └────┬─────┘
                                               │
                                               │ 6. Process
                                               ▼
                                        ┌─────────────┐
                                        │ Validation  │
                                        │  Worker     │
                                        └──────┬──────┘
                                               │
                                    7. Update Status
                                               │
                                               ▼
                                        ┌────────────┐
                                        │  Database  │
                                        └────────────┘
```

---

## Detailed Module Requirements

### 1. Communication Module

#### 1.1 Reports Submodule (Sprawozdania)

##### Functional Requirements

**REQ-COM-REP-001: Report Submission**
- **Priority**: CRITICAL
- **Description**: External users must be able to submit regulatory reports through the platform
- **Acceptance Criteria**:
  - Support for multiple file formats: XML, XBRL, PDF, ZIP
  - Maximum file size: 500MB per submission
  - Batch submission capability (up to 50 files)
  - Drag-and-drop interface
  - Progress indicator for upload
  - Resume capability for interrupted uploads
  - Automatic virus scanning on upload
  - Digital signature verification
  - Receipt confirmation with unique submission ID
  - Email notification upon successful submission

**REQ-COM-REP-002: Report Validation Engine**
- **Priority**: CRITICAL
- **Description**: Automatic validation of submitted reports against regulatory schemas
- **Acceptance Criteria**:
  - Real-time validation for XML/XBRL files
  - Schema validation against published UKNF schemas
  - Business rule validation (e.g., date ranges, numerical constraints)
  - Cross-field validation
  - Historical data consistency checks
  - Validation status tracking with timestamps
  - Detailed error reporting with line numbers and field references
  - Warning vs. error differentiation
  - Validation timeout: 24 hours maximum
  - Automatic retry mechanism for transient errors

**REQ-COM-REP-003: Validation Status Management**
- **Priority**: CRITICAL
- **Description**: Track and manage validation lifecycle of submitted reports
- **Validation Statuses**:
  1. **Robocze (Draft)**: Initial state upon file upload
  2. **Przekazane (Submitted)**: Validation process initiated
  3. **W trakcie (In Progress)**: Validation actively processing
  4. **Proces walidacji zakończony sukcesem (Validation Successful)**: No errors found
  5. **Błędy z reguł walidacji (Validation Errors)**: Business rule violations detected
  6. **Błąd techniczny w procesie (Technical Error)**: System error during processing
  7. **Błąd – przekroczono czas (Timeout Error)**: Processing exceeded 24-hour limit
  8. **Zakwestionowane przez UKNF (Challenged by UKNF)**: Manual rejection by UKNF staff
  
- **Acceptance Criteria**:
  - Automatic status transitions based on validation results
  - Manual status update capability for UKNF staff
  - Status history tracking with timestamps and user attribution
  - Real-time status notifications to submitter
  - Status-based filtering and search
  - Dashboard widgets showing status distribution
  - SLA tracking for validation completion time

**REQ-COM-REP-004: Report Version Control**
- **Priority**: HIGH
- **Description**: Maintain complete history of report submissions and corrections
- **Acceptance Criteria**:
  - Immutable storage of all submitted versions
  - Version numbering (v1.0, v1.1, v2.0, etc.)
  - Diff viewing between versions
  - Revert to previous version capability (UKNF only)
  - Version comparison reports
  - Annotation/notes on specific versions
  - Audit trail of all version changes

**REQ-COM-REP-005: Report Templates & Schemas**
- **Priority**: HIGH
- **Description**: Centralized management of report templates and validation schemas
- **Acceptance Criteria**:
  - Template library categorized by report type
  - Downloadable templates in multiple formats
  - Schema versioning and effective dates
  - Deprecation warnings for outdated schemas
  - Preview capability for templates
  - Template usage statistics
  - Automatic notification of new templates/schema versions

**REQ-COM-REP-006: Report Search & Filtering**
- **Priority**: HIGH
- **Description**: Advanced search capabilities across all submitted reports
- **Acceptance Criteria**:
  - Full-text search within report metadata
  - Filtering by: entity, date range, report type, status, assigned analyst
  - Saved search functionality
  - Export search results to CSV/Excel
  - Search performance: < 2 seconds for 90% of queries
  - Faceted search with result counts
  - Search history for users

**REQ-COM-REP-007: Report Analytics & Dashboards**
- **Priority**: MEDIUM
- **Description**: Visual analytics for report submission patterns and trends
- **Acceptance Criteria**:
  - Submission volume trends (daily, weekly, monthly)
  - Average validation time metrics
  - Error rate analysis by report type
  - Entity compliance scorecards
  - Deadline adherence tracking
  - Custom dashboard creation
  - Export charts and reports

**REQ-COM-REP-008: Bulk Operations**
- **Priority**: MEDIUM
- **Description**: Ability to perform actions on multiple reports simultaneously
- **Acceptance Criteria**:
  - Bulk status updates
  - Bulk assignment to analysts
  - Bulk download
  - Bulk export metadata
  - Confirmation prompts for destructive actions
  - Progress tracking for long-running operations
  - Rollback capability for reversible actions

#### 1.2 Matters Submodule (Sprawy)

##### Functional Requirements

**REQ-COM-MAT-001: Case Management System**
- **Priority**: CRITICAL
- **Description**: Structured workflow for managing regulatory cases and inquiries
- **Acceptance Criteria**:
  - Create case from: report issue, direct inquiry, or UKNF initiative
  - Unique case number generation (format: UKNF/YYYY/MM/XXXXX)
  - Case categorization: Inquiry, Clarification, Investigation, Enforcement, General
  - Priority levels: Low, Medium, High, Critical
  - Assignee management (internal UKNF staff)
  - Due date tracking with automated reminders
  - Related documents linking
  - Case status workflow (see REQ-COM-MAT-002)

**REQ-COM-MAT-002: Case Status Workflow**
- **Priority**: CRITICAL
- **Description**: Defined lifecycle for regulatory cases
- **Case Statuses**:
  1. **Nowy (New)**: Case created, awaiting assignment
  2. **Przypisany (Assigned)**: Assigned to UKNF staff member
  3. **W trakcie (In Progress)**: Active work ongoing
  4. **Oczekuje na odpowiedź (Awaiting Response)**: Waiting for external entity response
  5. **W zawieszeniu (Suspended)**: Temporarily paused
  6. **W trakcie weryfikacji (Under Review)**: Internal review by supervisor
  7. **Zamknięty (Closed)**: Case resolved
  8. **Archiwum (Archived)**: Long-term archival storage
  
- **Acceptance Criteria**:
  - Status transition rules with required fields
  - Automatic status changes based on triggers (e.g., deadline passed)
  - Status change audit log
  - Email notifications on status changes
  - Status-based access control
  - Reopening capability for closed cases (within 90 days)

**REQ-COM-MAT-003: Case Communication Thread**
- **Priority**: CRITICAL
- **Description**: Chronological communication history for each case
- **Acceptance Criteria**:
  - Threaded conversation view
  - Rich text editor for responses (formatting, lists, tables)
  - File attachments (multiple files, max 100MB per message)
  - @ mentions for notifying specific users
  - Draft saving
  - Read receipts
  - Response templates for common scenarios
  - Internal notes (visible only to UKNF staff)
  - External messages (visible to entity users)
  - Automatic timestamping and user attribution

**REQ-COM-MAT-004: Case Assignment & Routing**
- **Priority**: HIGH
- **Description**: Intelligent assignment and routing of cases
- **Acceptance Criteria**:
  - Manual assignment by supervisor
  - Auto-assignment based on rules (entity type, case category, workload)
  - Reassignment capability with reason logging
  - Workload balancing dashboard
  - Out-of-office handling (automatic reassignment)
  - Team-based assignment (multiple UKNF staff)
  - Escalation rules for overdue cases

**REQ-COM-MAT-005: Case SLA Tracking**
- **Priority**: HIGH
- **Description**: Monitor and enforce service level agreements
- **Acceptance Criteria**:
  - Configurable SLA by case type and priority
  - Visual indicators (green/yellow/red) for SLA status
  - Automated escalation on SLA breach
  - SLA pause capability (e.g., awaiting external response)
  - SLA reporting and analytics
  - Email alerts at 75%, 90%, and 100% of SLA time
  - Historical SLA compliance metrics

**REQ-COM-MAT-006: Case Templates**
- **Priority**: MEDIUM
- **Description**: Standardized templates for common case types
- **Acceptance Criteria**:
  - Template library management (UKNF admin only)
  - Pre-filled case attributes
  - Template-based case creation
  - Custom field support in templates
  - Template usage tracking
  - Template effectiveness analytics

**REQ-COM-MAT-007: Case Search & Reporting**
- **Priority**: HIGH
- **Description**: Comprehensive search and reporting capabilities
- **Acceptance Criteria**:
  - Advanced search: case number, entity, date range, status, assignee, keywords
  - Full-text search in case communications
  - Export case list to Excel/PDF
  - Custom report builder
  - Scheduled reports (weekly/monthly summaries)
  - Case statistics dashboard
  - Performance metrics by assignee/team

**REQ-COM-MAT-008: Case Relationships**
- **Priority**: MEDIUM
- **Description**: Link related cases and reports
- **Acceptance Criteria**:
  - Parent-child case relationships
  - Related case linking
  - Link to specific reports
  - Relationship visualization (graph view)
  - Impact analysis (show all affected cases)
  - Bulk operations on related cases

#### 1.3 Messages Submodule (Komunikaty)

##### Functional Requirements

**REQ-COM-MSG-001: Announcement System**
- **Priority**: HIGH
- **Description**: Broadcast important messages to all or specific groups of users
- **Acceptance Criteria**:
  - Create announcements with rich text formatting
  - Target audience selection: all users, specific entity types, individual entities
  - Scheduling: publish immediately or at specific date/time
  - Expiration date for time-sensitive announcements
  - Priority levels: Info, Important, Critical
  - Banner display for critical announcements
  - Read status tracking
  - Multi-language support (Polish and English)
  - Approval workflow for announcements (draft → review → published)

**REQ-COM-MSG-002: System Notifications**
- **Priority**: CRITICAL
- **Description**: Automated notifications for system events
- **Notification Types**:
  - Report submission confirmation
  - Validation completion (success or failure)
  - Case status changes
  - New messages in case threads
  - Deadline reminders
  - System maintenance alerts
  - Password expiration warnings
  - Access request status updates
  
- **Acceptance Criteria**:
  - In-app notification center
  - Email notifications (user-configurable)
  - SMS notifications for critical events (optional)
  - Notification preferences per notification type
  - Notification history (30 days retention)
  - Mark as read/unread functionality
  - Notification aggregation (daily digest option)
  - Real-time push notifications

**REQ-COM-MSG-003: Direct Messaging**
- **Priority**: MEDIUM
- **Description**: Secure messaging between UKNF staff and entity representatives
- **Acceptance Criteria**:
  - One-on-one messaging
  - Message history retention
  - File attachments
  - Read receipts
  - Typing indicators
  - Search within message history
  - Message archiving
  - Spam prevention and rate limiting

**REQ-COM-MSG-004: Notification Center Dashboard**
- **Priority**: MEDIUM
- **Description**: Centralized view of all notifications and messages
- **Acceptance Criteria**:
  - Unified inbox for all notification types
  - Filter by: type, priority, date, read status
  - Bulk actions: mark as read, delete, archive
  - Quick action buttons (e.g., view related case, download report)
  - Notification count badges
  - Customizable notification sounds
  - Do Not Disturb mode

**REQ-COM-MSG-005: Message Templates**
- **Priority**: LOW
- **Description**: Reusable message templates for common communications
- **Acceptance Criteria**:
  - Template library for UKNF staff
  - Variable substitution (e.g., {entity_name}, {case_number})
  - Template categories
  - Version control for templates
  - Preview before sending
  - Template usage statistics

#### 1.4 Library Submodule (Biblioteka)

##### Functional Requirements

**REQ-COM-LIB-001: Document Repository**
- **Priority**: HIGH
- **Description**: Central repository for regulatory documentation
- **Document Types**:
  - Legal acts and regulations
  - Guidelines and interpretations
  - Reporting instructions
  - Technical specifications
  - FAQs and help documents
  - Forms and templates
  - Training materials
  - Meeting minutes (public portions)
  
- **Acceptance Criteria**:
  - Hierarchical folder structure
  - Document versioning with change tracking
  - Metadata tagging: category, effective date, related regulation
  - Access control per document/folder
  - Download tracking and statistics
  - Document preview (PDF, Office formats)
  - Bulk upload capability

**REQ-COM-LIB-002: Document Search**
- **Priority**: HIGH
- **Description**: Advanced search within document repository
- **Acceptance Criteria**:
  - Full-text search including PDF content
  - Metadata filtering: date, category, document type, status
  - Search within specific folders
  - Relevance ranking
  - Search suggestions and autocomplete
  - Recent searches
  - Save search queries
  - Export search results

**REQ-COM-LIB-003: Document Lifecycle Management**
- **Priority**: HIGH
- **Description**: Manage document status and effective dates
- **Document Statuses**:
  - Draft
  - Under Review
  - Published
  - Superseded
  - Archived
  
- **Acceptance Criteria**:
  - Status workflow with approval process
  - Effective date and expiration date
  - Automatic status change on expiration
  - Notification of superseding documents
  - Audit trail of document changes
  - Approval history

**REQ-COM-LIB-004: Document Subscription**
- **Priority**: MEDIUM
- **Description**: Allow users to subscribe to document updates
- **Acceptance Criteria**:
  - Subscribe to specific folders or document types
  - Email notifications on new/updated documents
  - Subscription management dashboard
  - Unsubscribe link in emails
  - Digest option (daily/weekly summary)
  - RSS feed for document updates

**REQ-COM-LIB-005: Document Comments & Feedback**
- **Priority**: LOW
- **Description**: Allow users to provide feedback on documents
- **Acceptance Criteria**:
  - Comment threads on documents
  - Rating system (1-5 stars)
  - "Was this helpful?" buttons
  - Feedback analytics for UKNF
  - Moderation capability
  - Response from UKNF staff

**REQ-COM-LIB-006: Document Access Analytics**
- **Priority**: MEDIUM
- **Description**: Track document usage and popularity
- **Acceptance Criteria**:
  - View counts per document
  - Download statistics
  - Most popular documents report
  - Access by user type analysis
  - Trend analysis (seasonal patterns)
  - Low-usage document identification

---

### 2. Authentication & Authorization Module

#### 2.1 Authentication Submodule (Uwierzytelnienie)

##### Functional Requirements

**REQ-AUTH-AUT-001: Multi-Factor Authentication (MFA)**
- **Priority**: CRITICAL
- **Description**: Mandatory MFA for all user accounts
- **Supported Methods**:
  1. Time-based One-Time Password (TOTP) - Google Authenticator, Authy
  2. SMS one-time code
  3. Email one-time code
  4. Hardware security keys (FIDO2/WebAuthn) - YubiKey support
  5. Push notification (mobile app - future)
  
- **Acceptance Criteria**:
  - MFA enrollment during first login
  - Backup codes generation (10 codes)
  - MFA reset process (identity verification required)
  - Remember device for 30 days (optional, configurable)
  - MFA status visible to administrators
  - Audit log of MFA events
  - Grace period for MFA enrollment: 7 days

**REQ-AUTH-AUT-002: Single Sign-On (SSO)**
- **Priority**: HIGH
- **Description**: Unified authentication across all platform components
- **Acceptance Criteria**:
  - SAML 2.0 integration for internal UKNF staff (Active Directory)
  - OpenID Connect (OIDC) for external users
  - Seamless navigation between modules without re-authentication
  - Session duration: 8 hours of activity, 24 hours maximum
  - Concurrent session limit: 3 sessions per user
  - Session management dashboard (view and terminate active sessions)
  - Single logout across all sessions

**REQ-AUTH-AUT-003: Password Policy Enforcement**
- **Priority**: CRITICAL
- **Description**: Strong password requirements aligned with financial sector standards
- **Password Requirements**:
  - Minimum length: 12 characters
  - Maximum length: 128 characters
  - Must contain: uppercase, lowercase, number, special character
  - No dictionary words or common patterns
  - Cannot reuse last 5 passwords
  - Password history: 24 passwords
  - Maximum password age: 90 days
  - Account lockout: 5 failed attempts within 15 minutes
  - Lockout duration: 30 minutes (or manual unlock by administrator)
  
- **Acceptance Criteria**:
  - Real-time password strength indicator
  - Breach password checking (HaveIBeenPwned API)
  - Password expiration warnings (14, 7, 3, 1 days before)
  - Forced password change on first login
  - Administrator-initiated password reset (generates one-time link)
  - Self-service password reset (security questions + email verification)

**REQ-AUTH-AUT-004: Account Lockout & Security**
- **Priority**: CRITICAL
- **Description**: Protect against brute force and unauthorized access
- **Acceptance Criteria**:
  - Progressive delays after failed attempts (1s, 2s, 4s, 8s, 16s)
  - CAPTCHA after 3 failed attempts
  - IP-based rate limiting (100 requests/minute per IP)
  - Suspicious activity detection (login from new country, device)
  - Email notification on security events (failed login, password change, new device)
  - Security event dashboard for administrators
  - Whitelist IP ranges for UKNF offices
  - Automatic unlock after lockout period or manual unlock

**REQ-AUTH-AUT-005: Certificate-Based Authentication**
- **Priority**: HIGH
- **Description**: Support for qualified electronic signatures (Polish eIDAS)
- **Acceptance Criteria**:
  - Integration with Polish Trusted Profile (Profil Zaufany)
  - Support for qualified certificates from Polish certification authorities
  - Certificate validation (validity, revocation checking via OCSP/CRL)
  - Certificate-based login option for external users
  - Certificate information display (issuer, validity period, serial number)
  - Multiple certificates per user account
  - Certificate expiration warnings

**REQ-AUTH-AUT-006: Biometric Authentication (Future)**
- **Priority**: LOW
- **Description**: Support for biometric authentication methods
- **Supported Methods**:
  - Face ID / Touch ID on supported devices
  - Windows Hello integration
  
- **Acceptance Criteria**:
  - Optional biometric enrollment
  - Fallback to password + MFA
  - Device-specific enrollment
  - Privacy-preserving (biometric data stays on device)

#### 2.2 Access Requests Submodule (Wnioski)

##### Functional Requirements

**REQ-AUTH-REQ-001: New Account Registration**
- **Priority**: CRITICAL
- **Description**: Workflow for external entities to request platform access
- **Registration Process**:
  1. Entity identification (KRS number, REGON, NIP)
  2. Authorized representative information
  3. Contact details verification
  4. Upload supporting documents (authorization letter, ID scan)
  5. Terms of service acceptance
  6. GDPR consent
  7. Anti-money laundering (AML) declarations
  8. Submit for UKNF review
  
- **Acceptance Criteria**:
  - Multi-step registration form with progress indicator
  - Real-time validation of entity identifiers (KRS API integration)
  - Document upload with virus scanning
  - Email verification for contact addresses
  - Application status tracking
  - Average approval time: 3-5 business days
  - Automated rejection reasons
  - Resubmission capability after rejection

**REQ-AUTH-REQ-002: Access Request Approval Workflow**
- **Priority**: CRITICAL
- **Description**: Internal UKNF process for reviewing access requests
- **Approval Stages**:
  1. **Initial Review**: Completeness check, document verification
  2. **Background Check**: Entity status verification, sanctions screening
  3. **Supervisor Approval**: Final authorization
  4. **Account Provisioning**: Automatic account creation upon approval
  
- **Acceptance Criteria**:
  - Queue-based assignment to UKNF staff
  - Decision options: Approve, Reject, Request Additional Information
  - Rejection reason categories with free-text explanation
  - Request history and comments
  - SLA: 5 business days for initial response
  - Escalation after 10 days without response
  - Email notifications at each stage
  - Bulk approval capability

**REQ-AUTH-REQ-003: Additional User Requests**
- **Priority**: HIGH
- **Description**: Entity administrators can request additional user accounts
- **Acceptance Criteria**:
  - Request submitted by entity administrator
  - User details: name, email, phone, role, access level
  - Justification required for privileged roles
  - Authorization document upload
  - Simplified approval process (2-step: completeness, authorization)
  - Auto-approval for standard roles (optional configuration)
  - SLA: 2 business days

**REQ-AUTH-REQ-004: Access Modification Requests**
- **Priority**: HIGH
- **Description**: Request changes to existing user permissions
- **Acceptance Criteria**:
  - Request types: Role change, Permission addition/removal, Entity change
  - Current vs. requested access comparison view
  - Justification required
  - Approval by both entity administrator and UKNF (if privilege escalation)
  - Immediate effect upon approval
  - Audit trail of access changes
  - Notification to affected user

**REQ-AUTH-REQ-005: Access Revocation Requests**
- **Priority**: CRITICAL
- **Description**: Process for deactivating user accounts
- **Revocation Triggers**:
  - Entity administrator request (employee departure)
  - UKNF-initiated (security concern, entity closure)
  - Automatic (inactivity > 180 days)
  - Voluntary (user self-deactivation)
  
- **Acceptance Criteria**:
  - Immediate access suspension pending approval
  - Graceful session termination (within 5 minutes)
  - Data retention per GDPR (personal data anonymization)
  - Re-activation process within 90 days
  - Permanent deletion after retention period
  - Audit-compliant logging

**REQ-AUTH-REQ-006: Request Status Tracking**
- **Priority**: MEDIUM
- **Description**: Transparency into request processing status
- **Request Statuses**:
  - Submitted
  - Under Review
  - Additional Information Required
  - Approved
  - Rejected
  - Cancelled
  
- **Acceptance Criteria**:
  - Real-time status updates
  - Email notifications on status changes
  - Request details view
  - Communication thread with UKNF
  - Estimated completion date
  - Request cancellation (before approval)

#### 2.3 Authorization Submodule (Autoryzacja)

##### Functional Requirements

**REQ-AUTH-AUZ-001: Role-Based Access Control (RBAC)**
- **Priority**: CRITICAL
- **Description**: Comprehensive role and permission management system
- **Predefined Roles**:
  
  **External User Roles**:
  1. **Entity Administrator**
     - Manage entity users
     - View all entity submissions
     - Assign roles to entity users
     - Update entity profile
     - View audit logs for entity
  
  2. **Report Submitter**
     - Submit reports
     - View own submissions
     - Respond to validation errors
     - Download submission receipts
  
  3. **Authorized Representative**
     - All submitter permissions
     - Communicate on cases
     - Represent entity in official correspondence
     - Digital signature authority
  
  4. **Read-Only User**
     - View submitted reports (entity-wide)
     - View case communications
     - Download documents from library
     - No submission or response capabilities
  
  **Internal User Roles (UKNF)**:
  1. **System Administrator**
     - Full system access
     - User management across all entities
     - System configuration
     - Security settings
     - Backup and disaster recovery
  
  2. **Supervisor**
     - Review and approve submissions
     - Manage cases
     - Assign work to analysts
     - Create announcements
     - Access all entity data
  
  3. **Analyst**
     - Process assigned reports
     - Conduct validation reviews
     - Communicate with entities
     - Update case statuses
  
  4. **Communication Officer**
     - Manage announcements
     - Publish library documents
     - Moderate user feedback
     - Analytics and reporting
  
  5. **Auditor**
     - Read-only access to all data
     - Access audit logs
     - Generate compliance reports
     - No modification capabilities
  
- **Acceptance Criteria**:
  - Role hierarchy with inheritance
  - Custom role creation
  - Role assignment with effective dates
  - Multiple roles per user
  - Role conflict detection
  - Temporary role delegation (with expiration)

**REQ-AUTH-AUZ-002: Permission Management**
- **Priority**: CRITICAL
- **Description**: Granular permission control beyond roles
- **Permission Categories**:
  - **Data Permissions**: Create, Read, Update, Delete
  - **Module Access**: Communications, Administration, Reports
  - **Functional Permissions**: Approve, Reject, Export, Bulk Operations
  - **Data Scope**: Own data, Entity data, All data
  
- **Acceptance Criteria**:
  - Matrix-based permission assignment
  - Permission grouping
  - Negative permissions (explicit deny)
  - Permission inheritance from roles
  - Permission override capability
  - Effective permissions calculator (shows resultant permissions)
  - Permission audit trail

**REQ-AUTH-AUZ-003: Attribute-Based Access Control (ABAC)**
- **Priority**: MEDIUM
- **Description**: Dynamic access control based on user, resource, and environmental attributes
- **Supported Attributes**:
  - User attributes: Department, Clearance Level, Location
  - Resource attributes: Classification Level, Entity Owner, Creation Date
  - Environmental attributes: Time of day, IP address, Device type
  
- **Example Policies**:
  - "Analysts can only access cases assigned to them"
  - "External users can only view data for their own entity"
  - "Supervisors can approve requests only during business hours"
  - "High-sensitivity documents require MFA completed within last hour"
  
- **Acceptance Criteria**:
  - Policy definition language (or GUI builder)
  - Policy testing and simulation
  - Policy conflict resolution
  - Real-time policy evaluation
  - Policy audit logging

**REQ-AUTH-AUZ-004: Data-Level Security**
- **Priority**: CRITICAL
- **Description**: Ensure users can only access data they are authorized to see
- **Acceptance Criteria**:
  - Entity data isolation (multi-tenancy)
  - Row-level security in database
  - Field-level security (e.g., mask sensitive fields)
  - Data classification labels (Public, Internal, Confidential, Restricted)
  - Automatic data filtering based on user context
  - Security checks at API layer
  - Database-level security policies

**REQ-AUTH-AUZ-005: Delegation & Proxy Access**
- **Priority**: MEDIUM
- **Description**: Allow users to delegate access to others temporarily
- **Acceptance Criteria**:
  - Delegate specific permissions or entire role
  - Time-bound delegation (start and end dates)
  - Notification to both delegator and delegate
  - Delegation approval by administrator (for sensitive permissions)
  - Revocation capability
  - Audit trail of delegated actions (shows actual user and acting-as user)
  - Delegation limits (e.g., cannot delegate more than delegated)

**REQ-AUTH-AUZ-006: Access Review & Certification**
- **Priority**: HIGH
- **Description**: Periodic review of user access rights (compliance requirement)
- **Acceptance Criteria**:
  - Scheduled access reviews (quarterly or annually)
  - Entity administrator reviews for their users
  - UKNF administrator reviews for all users
  - Bulk certification (approve/revoke access)
  - Attestation reports
  - Automatic revocation of uncertified access
  - Reminder notifications
  - Exception handling for on-leave users

#### 2.4 Contact Form Submodule (Formularz kontaktowy)

##### Functional Requirements

**REQ-AUTH-CON-001: Public Contact Form**
- **Priority**: MEDIUM
- **Description**: Allow prospective users and general public to contact UKNF
- **Acceptance Criteria**:
  - Form fields: Name, Email, Phone, Entity Name (optional), Subject, Message
  - Inquiry categories: Access Request, Technical Support, General Inquiry, Complaint
  - CAPTCHA for spam prevention
  - File attachments (max 10MB, 5 files)
  - Email confirmation to submitter
  - Auto-response with ticket number
  - Submission without authentication required
  - Data retention: 2 years

**REQ-AUTH-CON-002: Contact Request Management**
- **Priority**: MEDIUM
- **Description**: Internal system for UKNF staff to manage contact form submissions
- **Acceptance Criteria**:
  - Queue-based inbox for contact requests
  - Assignment to staff members
  - Response templates
  - Status tracking: New, In Progress, Awaiting User, Resolved, Closed
  - Response tracking (ensure no request goes unanswered)
  - SLA: Response within 2 business days
  - Escalation for overdue requests
  - Convert to case if needed

**REQ-AUTH-CON-003: Contact History**
- **Priority**: LOW
- **Description**: Track history of communications from same submitter
- **Acceptance Criteria**:
  - Email-based linking of submissions
  - View previous submissions from same email
  - Notes and tags on submitter
  - Blocklist capability (for spam/abuse)
  - Analytics: Common inquiry topics, response times

---

### 3. Administrative Module

#### 3.1 User Management Submodule (Zarządzanie użytkownikami)

##### Functional Requirements

**REQ-ADM-USR-001: User Lifecycle Management**
- **Priority**: CRITICAL
- **Description**: Complete user account management from creation to deletion
- **User Lifecycle Stages**:
  1. **Pending**: Access request submitted, awaiting approval
  2. **Active**: Account active and accessible
  3. **Locked**: Temporarily locked (failed logins, admin action)
  4. **Suspended**: Temporary suspension (investigation, policy violation)
  5. **Inactive**: No activity for extended period (auto-suspend after 180 days)
  6. **Deactivated**: Account disabled (user departure, entity closure)
  7. **Deleted**: Account permanently deleted (GDPR compliance)
  
- **Acceptance Criteria**:
  - Automated status transitions based on triggers
  - Manual status changes by administrators
  - Status change notifications
  - Grace periods before automatic actions
  - Reactivation workflows
  - Audit trail of all status changes

**REQ-ADM-USR-002: User Profile Management**
- **Priority**: CRITICAL
- **Description**: Maintain comprehensive user profiles
- **Profile Information**:
  - **Personal Data**: First name, Last name, Middle name
  - **Contact Information**: Email (primary, verified), Phone (mobile, office), Fax
  - **Professional Information**: Job title, Department, Employee ID
  - **Entity Association**: Linked entity/entities, Role within entity
  - **Account Information**: Username, Last login, Created date, Modified date
  - **Security Information**: MFA status, Password last changed, Failed login count
  - **Preferences**: Language, Timezone, Notification settings, UI theme
  - **Legal**: GDPR consent date, Terms acceptance date
  
- **Acceptance Criteria**:
  - Self-service profile editing (limited fields)
  - Administrator can edit all fields
  - Email change requires verification
  - Profile photo upload (avatar)
  - Profile completeness indicator
  - Data validation and format checking
  - Profile history (view previous values)

**REQ-ADM-USR-003: User Search & Filtering**
- **Priority**: HIGH
- **Description**: Efficient user lookup and management
- **Acceptance Criteria**:
  - Search by: Name, Email, Username, Entity, Role, Status
  - Advanced filters: Last login date, Creation date, MFA status, Account age
  - Saved filters
  - Export user list (CSV, Excel) with selected fields
  - Bulk actions: Status change, Role assignment, Password reset, Send notification
  - User statistics dashboard
  - Search performance: < 1 second for 100K users

**REQ-ADM-USR-004: User Activity Monitoring**
- **Priority**: HIGH
- **Description**: Track and analyze user behavior for security and compliance
- **Monitored Activities**:
  - Login/logout events
  - Failed login attempts
  - Password changes
  - MFA events
  - Profile modifications
  - Data access (read, download)
  - Data modifications (create, update, delete)
  - Administrative actions
  - Session information (IP, device, browser, location)
  
- **Acceptance Criteria**:
  - Real-time activity logging
  - Activity dashboard per user
  - Anomaly detection (unusual activity patterns)
  - Geolocation tracking
  - Device fingerprinting
  - Session recording (actions, not keystrokes)
  - Activity retention: 7 years (regulatory requirement)
  - Privacy-compliant logging (no sensitive data in logs)

**REQ-ADM-USR-005: Bulk User Operations**
- **Priority**: MEDIUM
- **Description**: Efficiently manage large numbers of users
- **Bulk Operations**:
  - User import via CSV/Excel
  - Bulk role assignment
  - Bulk permission changes
  - Bulk account activation/deactivation
  - Bulk password reset (sends reset emails)
  - Bulk notification sending
  
- **Acceptance Criteria**:
  - Template download for imports
  - Data validation before import
  - Preview changes before committing
  - Error handling and reporting
  - Partial success handling
  - Rollback capability
  - Progress tracking for long operations
  - Email confirmation upon completion

**REQ-ADM-USR-006: User Impersonation (for Support)**
- **Priority**: MEDIUM
- **Description**: Allow administrators to view system as specific user (troubleshooting)
- **Acceptance Criteria**:
  - Permission required: IMPERSONATE_USER
  - Select user to impersonate
  - Clear visual indicator of impersonation mode
  - All actions logged with actual admin user
  - Restricted actions during impersonation (no password changes, no destructive actions)
  - Exit impersonation at any time
  - Time limit: 1 hour per impersonation session
  - Notification to impersonated user (optional, configurable)
  - Audit log of impersonation sessions

#### 3.2 Password Policies Submodule (Polityka haseł)

##### Functional Requirements

**REQ-ADM-PWD-001: Configurable Password Policies**
- **Priority**: HIGH
- **Description**: Allow administrators to configure password requirements
- **Configurable Parameters**:
  - Minimum length (8-32 characters)
  - Maximum length (32-128 characters)
  - Character requirements: Uppercase, Lowercase, Digits, Special characters
  - Minimum character type diversity (e.g., must include 3 out of 4 types)
  - Dictionary word checking (enable/disable)
  - Password history count (prevent reuse of last N passwords)
  - Maximum password age (days)
  - Password expiration warning period (days)
  - Account lockout threshold (failed attempts)
  - Lockout duration (minutes)
  - Password reset link validity (hours)
  
- **Acceptance Criteria**:
  - Policy configuration interface
  - Multiple policies for different user types (e.g., stricter for UKNF staff)
  - Policy preview and testing
  - Policy effective date (allow scheduled policy changes)
  - Policy history and versioning
  - User notification of policy changes
  - Grace period for compliance with new policy

**REQ-ADM-PWD-002: Password Strength Meter**
- **Priority**: MEDIUM
- **Description**: Visual feedback on password strength during creation/change
- **Acceptance Criteria**:
  - Real-time strength calculation
  - Visual indicator: Weak (red), Fair (orange), Good (yellow), Strong (green), Very Strong (dark green)
  - Entropy calculation
  - Pattern detection (keyboard patterns, repeating characters)
  - Feedback messages (e.g., "Add more character types", "Avoid common patterns")
  - Minimum strength requirement enforcement
  - Bypass option for administrators (with justification)

**REQ-ADM-PWD-003: Compromised Password Detection**
- **Priority**: HIGH
- **Description**: Prevent use of known compromised passwords
- **Acceptance Criteria**:
  - Integration with HaveIBeenPwned API (k-Anonymity model for privacy)
  - Check password against breach database during creation/change
  - Block compromised passwords
  - User-friendly error message (without revealing breach details)
  - Offline mode: Use local breach database
  - Daily sync of breach database
  - Configurable sensitivity (block if seen in X or more breaches)

**REQ-ADM-PWD-004: Password Reset Workflow**
- **Priority**: CRITICAL
- **Description**: Secure and user-friendly password reset process
- **Self-Service Reset**:
  1. User enters email/username
  2. Security questions (optional, configurable)
  3. Email with one-time reset link
  4. Link valid for 2 hours
  5. User sets new password
  6. Confirmation email sent
  
- **Administrator Reset**:
  1. Administrator initiates reset for user
  2. User receives reset link via email
  3. User sets new password
  4. Optional: Force password change at next login
  
- **Acceptance Criteria**:
  - Rate limiting (max 3 reset requests per hour per email)
  - CAPTCHA after multiple attempts
  - Link expiration
  - One-time use of reset links
  - Invalidate all sessions after password change
  - Email notification to user (even if they didn't request reset - security)
  - Audit log of reset requests

**REQ-ADM-PWD-005: Password Expiration Management**
- **Priority**: HIGH
- **Description**: Enforce periodic password changes
- **Acceptance Criteria**:
  - Configurable password age (e.g., 90 days)
  - Warning notifications (14, 7, 3, 1 days before expiration)
  - Grace period after expiration (e.g., 5 days)
  - Forced password change after grace period (block login until changed)
  - Exclude service accounts from expiration (optional)
  - Administrator can extend expiration (with justification)
  - Exception requests workflow
  - Report of users with expiring/expired passwords

**REQ-ADM-PWD-006: Account Lockout Policy**
- **Priority**: CRITICAL
- **Description**: Protect against brute force attacks
- **Lockout Triggers**:
  - Failed login attempts (threshold configurable)
  - Multiple MFA failures
  - Multiple password reset attempts
  - Suspicious activity patterns
  
- **Acceptance Criteria**:
  - Configurable lockout threshold (3-10 attempts)
  - Configurable lockout duration (15-60 minutes)
  - Progressive lockout (increase duration with repeated lockouts)
  - IP-based lockout (block IP after threshold)
  - Manual unlock by administrator
  - Self-service unlock via email verification (optional)
  - Email notification on lockout
  - Lockout analytics dashboard

#### 3.3 Roles & Permissions Submodule (Role i uprawnienia)

##### Functional Requirements

**REQ-ADM-ROL-001: Role Management System**
- **Priority**: CRITICAL
- **Description**: Comprehensive role definition and assignment
- **Role Properties**:
  - Role name (unique identifier)
  - Display name (localized)
  - Description
  - Role type: System-defined, Custom
  - Status: Active, Deprecated
  - Category: External, Internal, Mixed
  - Parent role (for inheritance)
  - Effective date range
  
- **Acceptance Criteria**:
  - Create/edit/delete custom roles
  - System-defined roles cannot be deleted (can be disabled)
  - Role cloning (copy from existing role)
  - Role hierarchy visualization
  - Role assignment to users
  - Bulk role assignment
  - Role assignment approval workflow (for sensitive roles)
  - Audit trail of role changes

**REQ-ADM-ROL-002: Permission Matrix**
- **Priority**: CRITICAL
- **Description**: Granular permission management
- **Permission Structure**:
  ```
  Module → Sub-Module → Resource → Action → Scope
  
  Example:
  Communication → Reports → Submission → Create → Own Entity
  Communication → Reports → Submission → View → All Entities (UKNF only)
  Administration → Users → User Account → Delete → Own Entity
  ```
  
- **Actions**:
  - Create
  - Read/View
  - Update/Edit
  - Delete
  - Export
  - Import
  - Approve
  - Reject
  - Assign
  - Share
  
- **Scopes**:
  - Own (user's own data)
  - Entity (user's entity data)
  - Assigned (data assigned to user)
  - All (all data - typically UKNF only)
  
- **Acceptance Criteria**:
  - Matrix-based permission UI
  - Bulk permission assignment
  - Permission templates
  - Permission inheritance from parent role
  - Permission override capability
  - Negative permissions (explicit deny overrides allow)
  - Effective permission calculator
  - Permission conflict detection and resolution

**REQ-ADM-ROL-003: Role Assignment Management**
- **Priority**: HIGH
- **Description**: Manage role assignments to users
- **Acceptance Criteria**:
  - Assign single or multiple roles to user
  - Role assignment with effective dates (start and end)
  - Temporary role assignment
  - Role assignment justification (required for sensitive roles)
  - Approval workflow for privileged role assignments
  - Automatic role removal on end date
  - Role assignment notifications
  - Role assignment audit trail
  - View all users with specific role
  - Role conflict detection (incompatible roles)

**REQ-ADM-ROL-004: Role Hierarchy & Inheritance**
- **Priority**: MEDIUM
- **Description**: Support role inheritance to simplify management
- **Acceptance Criteria**:
  - Parent-child role relationships
  - Child role inherits all parent permissions
  - Child role can add permissions (not remove parent permissions)
  - Multiple inheritance support
  - Inheritance visualization (tree view)
  - Circular dependency detection
  - Inheritance conflict resolution rules
  - Override capability for specific permissions

**REQ-ADM-ROL-005: Role Templates**
- **Priority**: MEDIUM
- **Description**: Pre-defined role templates for common scenarios
- **Predefined Templates**:
  - New Entity Basic Access
  - Entity Administrator
  - Report Submitter
  - Entity Auditor
  - UKNF Analyst
  - UKNF Supervisor
  - System Administrator
  
- **Acceptance Criteria**:
  - Template library management
  - Create custom templates
  - Apply template to user (creates role assignment)
  - Template versioning
  - Template usage tracking
  - Template effectiveness analytics

**REQ-ADM-ROL-006: Separation of Duties (SoD)**
- **Priority**: HIGH
- **Description**: Enforce segregation of duties for compliance
- **Conflicting Roles Examples**:
  - Report Submitter + Report Approver (same entity)
  - User Manager + Security Auditor
  - Developer + Production Administrator
  
- **Acceptance Criteria**:
  - Define SoD rules
  - Real-time SoD conflict detection
  - Block conflicting role assignments
  - Exception approval workflow (with justification and time limit)
  - SoD violation reports
  - Regular SoD compliance audits
  - Alert administrators of violations

**REQ-ADM-ROL-007: Role Analytics & Reporting**
- **Priority**: MEDIUM
- **Description**: Insights into role usage and effectiveness
- **Reports**:
  - Role usage by entity
  - Users per role
  - Orphaned roles (no users assigned)
  - Over-privileged users (excessive role assignments)
  - Under-utilized permissions
  - Role changes over time
  - Compliance reports (access certification)
  
- **Acceptance Criteria**:
  - Interactive dashboards
  - Export reports (PDF, Excel)
  - Scheduled report delivery
  - Custom report builder
  - Trend analysis

#### 3.4 Entity Database & Data Updater Submodule (Baza Podmiotów + Aktualizator danych podmiotu)

##### Functional Requirements

**REQ-ADM-ENT-001: Entity Registry**
- **Priority**: CRITICAL
- **Description**: Central registry of all supervised entities
- **Entity Information**:
  - **Basic Information**:
    - Entity name (full legal name)
    - Short name / trading name
    - Entity type (Bank, Insurance Company, Investment Fund, Brokerage, Pension Fund, Credit Union, etc.)
    - Legal form (S.A., Sp. z o.o., etc.)
    - KRS number (National Court Register)
    - REGON number (National Business Registry)
    - NIP number (Tax ID)
    - LEI code (Legal Entity Identifier)
  
  - **Contact Information**:
    - Registered address
    - Mailing address (if different)
    - Office address
    - Phone numbers
    - Fax number
    - General email
    - Website URL
  
  - **Supervision Details**:
    - Supervision status (Active, Suspended, Terminated)
    - Supervision start date
    - License/permit numbers
    - Scope of supervision
    - Assigned supervisor (UKNF staff)
    - Risk classification (Low, Medium, High)
    - Supervision category
  
  - **Management Board**:
    - Board members (names, roles, appointment dates)
    - Authorized signatories
    - Contact persons for regulatory matters
  
  - **Financial Data**:
    - Total assets
    - Revenue
    - Number of employees
    - Fiscal year end
  
  - **Operational Data**:
    - Number of branches
    - Geographical coverage
    - Services offered
    - Customer base size
  
  - **Related Entities**:
    - Parent company
    - Subsidiaries
    - Affiliated entities
    - Group structure
  
- **Acceptance Criteria**:
  - Comprehensive data model covering all entity types
  - Custom fields per entity type
  - Data validation rules
  - Mandatory field enforcement
  - Entity profile completeness indicator
  - Document attachments (licenses, permits, registration certificates)
  - Profile history (view previous versions)

**REQ-ADM-ENT-002: Entity Data Validation & Verification**
- **Priority**: HIGH
- **Description**: Ensure accuracy and currency of entity data
- **Validation Methods**:
  - Real-time validation against external registries:
    - KRS (National Court Register API)
    - REGON (Statistics Poland API)
    - NIP (Tax Office verification)
  - Business rule validation (e.g., LEI format, phone number format)
  - Duplicate detection (prevent duplicate entity creation)
  
- **Acceptance Criteria**:
  - Automated validation on data entry
  - API integration with Polish registries
  - Fallback for API unavailability (manual verification)
  - Validation status indicators (Verified, Pending, Failed)
  - Re-validation schedule (quarterly)
  - Discrepancy alerts (data mismatch with external sources)
  - Manual override capability (with justification)

**REQ-ADM-ENT-003: Entity Lifecycle Management**
- **Priority**: HIGH
- **Description**: Manage entity status throughout supervision lifecycle
- **Entity Statuses**:
  1. **Pending Registration**: Initial registration in progress
  2. **Active**: Currently supervised entity
  3. **Under Investigation**: Regulatory investigation ongoing
  4. **Suspended**: Temporary suspension of operations
  5. **Wind-Down**: Entity in liquidation process
  6. **Terminated**: Supervision ended (license revoked, bankruptcy)
  7. **Merged**: Entity merged into another entity
  8. **Historical**: Archived entity (for historical records)
  
- **Acceptance Criteria**:
  - Status workflow with required documentation
  - Status change approval (supervisor or administrator)
  - Status change notifications to entity users
  - Status-based access control (e.g., terminated entities have read-only access)
  - Status transition history
  - Impact analysis for status changes (affected users, reports, cases)

**REQ-ADM-ENT-004: Automatic Data Updater**
- **Priority**: HIGH
- **Description**: Automated synchronization with external data sources
- **Update Sources**:
  - KRS API (company data, management board changes)
  - REGON API (statistical data)
  - Public registers (license status, sanctions)
  - Entity-provided updates (via self-service portal)
  
- **Update Schedule**:
  - Critical data: Daily (supervision status, license status)
  - Basic data: Weekly (contact information, management board)
  - Statistical data: Monthly (financial indicators, employee counts)
  - Comprehensive refresh: Quarterly
  
- **Acceptance Criteria**:
  - Scheduled background jobs
  - Change detection (only update if data has changed)
  - Change notifications to administrators
  - Conflict resolution (external source vs. manually entered data)
  - Audit trail of automatic updates
  - Manual refresh trigger
  - Error handling and retry mechanism
  - Update statistics dashboard

**REQ-ADM-ENT-005: Entity Self-Service Data Updates**
- **Priority**: MEDIUM
- **Description**: Allow entity administrators to update their organization data
- **Updatable Fields**:
  - Contact information (addresses, phones, emails)
  - Authorized representatives
  - Organizational structure
  - Service offerings
  - Website URL
  
- **Non-Updatable Fields** (UKNF only):
  - Entity name
  - Registration numbers (KRS, REGON, NIP)
  - Entity type
  - Supervision status
  - Risk classification
  
- **Acceptance Criteria**:
  - Self-service portal for entity administrators
  - Pending changes workflow (submit for UKNF approval)
  - Supporting documentation upload
  - Approval notification
  - Automatic update upon approval
  - Update history visible to entity
  - Audit trail

**REQ-ADM-ENT-006: Entity Search & Filtering**
- **Priority**: HIGH
- **Description**: Efficient entity lookup and management
- **Acceptance Criteria**:
  - Search by: Name, KRS, REGON, NIP, LEI, Entity Type, Status
  - Advanced filters: Supervision date range, Risk classification, Assigned supervisor, Asset size range
  - Full-text search across all entity fields
  - Saved searches
  - Export entity list (CSV, Excel, PDF)
  - Entity comparison view (side-by-side comparison)
  - Map view (geographical distribution)
  - Statistical dashboards (entities by type, by status, by region)

**REQ-ADM-ENT-007: Entity Relationships & Group Structure**
- **Priority**: MEDIUM
- **Description**: Visualize and manage entity relationships
- **Acceptance Criteria**:
  - Define relationship types (Parent, Subsidiary, Affiliate, Joint Venture)
  - Ownership percentage
  - Relationship effective dates
  - Visual org chart of entity groups
  - Consolidated view (roll-up data across group)
  - Impact analysis (changes affecting multiple entities)
  - Cross-entity reporting

**REQ-ADM-ENT-008: Entity Risk Assessment**
- **Priority**: MEDIUM
- **Description**: Maintain risk profiles for supervised entities
- **Risk Factors**:
  - Financial stability indicators
  - Compliance history
  - Governance quality
  - Operational complexity
  - Market position
  - Systemic importance
  
- **Acceptance Criteria**:
  - Risk scoring model (1-10 or Low/Medium/High/Critical)
  - Manual risk assessment entry
  - Automated risk indicators from reports
  - Risk trend analysis over time
  - Risk-based supervision planning
  - Risk heatmap visualization
  - Alerts for risk elevation

---

## User Interface Requirements

### Enterprise-Grade UI Design Principles

#### Design System Foundation

**REQ-UI-001: Design System Components**
- **Component Library**: shadcn/ui with custom UKNF branding
- **Typography**: 
  - Primary font: Inter or similar professional sans-serif
  - Monospace font: JetBrains Mono (for technical data)
  - Font sizes: Scale from 12px to 48px
  - Line heights optimized for readability
  
- **Color Palette**:
  - **Primary**: Professional blue (#0F3A8C or custom UKNF brand color)
  - **Secondary**: Complementary teal (#0D7377)
  - **Success**: Green (#10B981)
  - **Warning**: Amber (#F59E0B)
  - **Error**: Red (#EF4444)
  - **Neutral**: Gray scale (#1F2937 to #F9FAFB)
  - **Background**: White primary, light gray secondary (#F3F4F6)
  
- **Spacing System**: 4px base unit (0.25rem), scale: 4, 8, 12, 16, 24, 32, 48, 64
- **Shadows**: Subtle elevation shadows for depth
- **Border Radius**: Consistent rounding (4px for inputs, 8px for cards, 12px for modals)
- **Icons**: Lucide React or Heroicons for consistency

**REQ-UI-002: Responsive Design**
- **Breakpoints**:
  - Mobile: < 640px
  - Tablet: 640px - 1024px
  - Desktop: 1024px - 1440px
  - Large Desktop: > 1440px
  
- **Acceptance Criteria**:
  - Mobile-first approach
  - Touch-friendly targets (minimum 44x44px)
  - Responsive tables (stack or horizontal scroll)
  - Collapsible navigation on mobile
  - Optimized layouts for each breakpoint
  - Test on iPhone, iPad, Android devices
  - Progressive enhancement

**REQ-UI-003: Navigation & Information Architecture**
- **Primary Navigation**:
  - Top navigation bar (horizontal)
  - Logo (left), User menu (right)
  - Module switcher (Communication, Administration)
  - Notifications icon with badge
  - Search icon (global search)
  
- **Secondary Navigation**:
  - Left sidebar for sub-modules
  - Collapsible sections
  - Active state highlighting
  - Breadcrumbs for deep navigation
  
- **Acceptance Criteria**:
  - Maximum 3 levels of navigation depth
  - Clear visual hierarchy
  - Persistent navigation (always visible)
  - Keyboard navigation support (Tab, Enter, Esc)
  - Mega menu for complex sections (optional)

**REQ-UI-004: Dashboard Design**
- **Dashboard Components**:
  - **Key Metrics Cards**: Large numbers with trend indicators
  - **Charts**: Line, bar, pie, donut (using Recharts or Chart.js)
  - **Recent Activity Feed**: Chronological list of events
  - **Quick Actions**: Prominent buttons for common tasks
  - **Status Widgets**: Real-time status of reports, cases, users
  - **Calendar/Timeline**: Upcoming deadlines and events
  
- **Dashboard Types**:
  - External User Dashboard: Focus on submission status, deadlines, notifications
  - UKNF Analyst Dashboard: Workload, pending tasks, case statuses
  - Administrator Dashboard: System health, user activity, security events
  
- **Acceptance Criteria**:
  - Customizable dashboards (drag-and-drop widgets)
  - Widget library
  - Real-time data updates (WebSocket or polling)
  - Export dashboard as PDF/image
  - Mobile-optimized dashboard (stacked widgets)
  - Personalization (save layout per user)

**REQ-UI-005: Forms & Data Entry**
- **Form Best Practices**:
  - Clear labels above fields
  - Placeholder text for format guidance
  - Inline validation with immediate feedback
  - Error messages below fields (red text + icon)
  - Required field indicators (asterisk)
  - Field help text (tooltip or below field)
  - Character counters for text fields
  - Auto-save for long forms (draft saving)
  - Progress indicators for multi-step forms
  
- **Input Types**:
  - Text inputs (single-line, multi-line)
  - Number inputs with increment/decrement
  - Date pickers with calendar widget
  - Time pickers
  - Dropdowns (single and multi-select)
  - Autocomplete with search
  - Radio buttons (up to 5 options)
  - Checkboxes
  - File upload (drag-and-drop zone)
  - Rich text editor (for formatted content)
  
- **Acceptance Criteria**:
  - Tab order follows visual order
  - Enter key submits form
  - Esc key cancels/closes
  - Unsaved changes warning
  - Success confirmation after submission
  - Loading states during submission
  - Disable submit button during processing
  - Form reset option

**REQ-UI-006: Tables & Data Grids**
- **Table Features**:
  - Sortable columns (click header to sort)
  - Filterable columns (search/filter per column)
  - Pagination (10, 25, 50, 100, All rows)
  - Row selection (checkbox for bulk actions)
  - Row actions menu (kebab menu or hover actions)
  - Expandable rows (for nested data)
  - Fixed header (scroll table content)
  - Column visibility toggle
  - Column resizing
  - Export table data (CSV, Excel, PDF)
  
- **Mobile Tables**:
  - Card view (each row as a card)
  - Horizontal scroll with fixed first column
  - Simplified view (show only key columns)
  
- **Acceptance Criteria**:
  - Performance: Handle 10,000+ rows with virtualization
  - Loading skeletons while data fetches
  - Empty state message
  - Error state handling
  - Keyboard navigation (arrow keys, Tab)
  - Accessibility: Screen reader support

**REQ-UI-007: Modals & Dialogs**
- **Modal Types**:
  - Confirmation dialog (Are you sure?)
  - Form modal (Create/Edit entity)
  - Information modal (View details)
  - Alert modal (Warning, Error)
  
- **Design Specifications**:
  - Overlay backdrop (semi-transparent black)
  - Centered modal with max-width
  - Close button (X in top-right)
  - Header, body, footer sections
  - Primary and secondary action buttons
  - Esc key closes modal
  - Click outside closes (configurable)
  
- **Acceptance Criteria**:
  - Modal stacking (up to 2 levels)
  - Focus trap within modal
  - Return focus to trigger element on close
  - Smooth open/close animations
  - Scrollable body if content overflows
  - Mobile-friendly (full-screen on mobile)

**REQ-UI-008: Notifications & Alerts**
- **Notification Types**:
  - **Toast/Snackbar**: Temporary message (5 seconds)
  - **Banner**: Persistent message at top of page
  - **Inline Alert**: Within page content
  - **Badge**: Count indicator (e.g., notification bell)
  
- **Severity Levels**:
  - Info (blue): Informational message
  - Success (green): Action completed successfully
  - Warning (amber): Caution required
  - Error (red): Action failed or error occurred
  
- **Acceptance Criteria**:
  - Auto-dismiss after timeout (except errors)
  - Manual dismiss option (X button)
  - Stack multiple notifications
  - Action buttons within notification (e.g., "Undo", "View Details")
  - Sound notification (optional, user preference)
  - Notification center (history of all notifications)

**REQ-UI-009: Loading & Empty States**
- **Loading States**:
  - Skeleton screens (content placeholder)
  - Spinner (for small areas)
  - Progress bar (for determinate progress)
  - Loading overlay (for full page/modal)
  
- **Empty States**:
  - Illustration or icon
  - Descriptive message
  - Call-to-action button (e.g., "Create First Report")
  - Help text or link to documentation
  
- **Acceptance Criteria**:
  - Loading states shown within 100ms
  - Empty states for all list/table views
  - Error states with retry option
  - Graceful degradation (show partial data if available)

**REQ-UI-010: Accessibility Features (WCAG 2.1 AA)**
- See detailed section below

#### Page Layouts

**REQ-UI-011: Report Submission Page**
- **Layout**:
  - Step indicator (1. Select Report Type → 2. Upload Files → 3. Review → 4. Submit)
  - Large file upload dropzone
  - File list with status, size, remove option
  - Report metadata form (date, period, entity, notes)
  - Terms acceptance checkbox
  - Submit button (disabled until validation passes)
  
- **Acceptance Criteria**:
  - Drag-and-drop file upload
  - Progress bars for each file
  - Virus scan status indicator
  - Preview uploaded files (if applicable)
  - Clear error messages if validation fails
  - Success page with submission ID and receipt download

**REQ-UI-012: Case Management Page**
- **Layout**:
  - Left: Case list (filterable, searchable)
  - Right: Case details pane
  - Case header: Case number, status badge, priority, assignee
  - Tabbed interface: Overview, Communications, Related Documents, History
  - Action buttons: Update Status, Assign, Close Case
  
- **Acceptance Criteria**:
  - Split-pane layout (resizable)
  - Case list updates in real-time
  - Communication thread with timestamps
  - Rich text editor for responses
  - File attachment in communications
  - Activity timeline showing all events

**REQ-UI-013: User Management Page**
- **Layout**:
  - Top: Search and filter bar
  - Table: User list with columns (Name, Email, Entity, Role, Status, Last Login)
  - Row actions: Edit, Deactivate, Reset Password, View Activity
  - Bulk actions toolbar (appears when rows selected)
  - Right-side drawer: User details (opens on row click)
  
- **Acceptance Criteria**:
  - Inline editing for quick updates
  - User detail drawer with tabs (Profile, Roles, Activity, Security)
  - Status badges with color coding
  - Quick filters (Active Users, Locked Accounts, New Requests)
  - Export selected users

**REQ-UI-014: Analytics & Reports Page**
- **Layout**:
  - Top: Date range picker, entity filter, report type selector
  - Grid layout for charts/widgets
  - Responsive grid (3 columns on desktop, 2 on tablet, 1 on mobile)
  - Each widget with mini-toolbar (expand, export, settings)
  
- **Acceptance Criteria**:
  - Interactive charts (hover for details, click to drill down)
  - Real-time data updates
  - Export individual charts or full report
  - Save custom report layouts
  - Share reports via link

---

## Security & Compliance Requirements

### Security Requirements

**REQ-SEC-001: Authentication Security**
- **Acceptance Criteria**:
  - TLS 1.3 for all connections
  - Certificate pinning for mobile apps
  - JWT tokens with short expiration (15 minutes access, 7 days refresh)
  - Secure token storage (HttpOnly cookies or secure storage)
  - Token rotation on each refresh
  - Revocation mechanism for compromised tokens
  - Session fixation prevention
  - CSRF protection on all state-changing requests
  - Brute force protection (see password policy)

**REQ-SEC-002: Data Encryption**
- **Encryption at Rest**:
  - Database: PostgreSQL TDE (Transparent Data Encryption) using AES-256
  - File Storage: MinIO encryption using AES-256-GCM
  - Backups: Encrypted using separate keys
  - Encryption key management: Hardware Security Module (HSM) or KMS
  
- **Encryption in Transit**:
  - TLS 1.3 for all HTTP traffic
  - TLS 1.2 minimum (for legacy support)
  - Perfect Forward Secrecy (PFS) enabled
  - Strong cipher suites only
  - Certificate validation
  
- **Encryption at Application Level**:
  - Personally Identifiable Information (PII) encrypted in database (field-level encryption)
  - Encryption keys rotated annually
  - Separate encryption keys per entity (multi-tenancy)
  
- **Acceptance Criteria**:
  - No plaintext sensitive data in logs
  - No sensitive data in URLs (query parameters)
  - Encryption verification in security audits
  - Key rotation procedures documented
  - Automated key rotation where possible

**REQ-SEC-003: Input Validation & Output Encoding**
- **Input Validation**:
  - Server-side validation for all inputs
  - Whitelist validation (allow known good)
  - Type checking and range validation
  - Length limits on all text fields
  - File type validation (MIME type and magic bytes)
  - File size limits
  - SQL injection prevention (parameterized queries)
  - NoSQL injection prevention
  - LDAP injection prevention
  - Command injection prevention
  - XML External Entity (XXE) prevention
  
- **Output Encoding**:
  - Context-aware output encoding (HTML, JavaScript, URL, CSS)
  - XSS prevention in all user-generated content
  - Content Security Policy (CSP) headers
  - X-Frame-Options header (clickjacking prevention)
  - X-Content-Type-Options header
  
- **Acceptance Criteria**:
  - OWASP Top 10 vulnerability testing
  - Automated security scanning in CI/CD
  - Penetration testing annually
  - Bug bounty program (optional)

**REQ-SEC-004: Audit Logging**
- **Logged Events**:
  - Authentication events (login, logout, failed attempts)
  - Authorization changes (role assignments, permission changes)
  - Data access (view, download sensitive data)
  - Data modifications (create, update, delete)
  - Administrative actions (user creation, configuration changes)
  - Security events (lockouts, MFA changes, password resets)
  - System events (service start/stop, errors)
  
- **Log Contents**:
  - Timestamp (UTC, with milliseconds)
  - User ID and username
  - Session ID
  - IP address
  - User agent
  - Action performed
  - Resource accessed
  - Result (success/failure)
  - Additional context (entity, case number, etc.)
  
- **Log Security**:
  - Logs immutable (write-only)
  - Log integrity verification (cryptographic hashing)
  - Log encryption at rest
  - Separate log storage (centralized logging server)
  - Access control on logs (auditors only)
  - Log retention: 7 years (regulatory requirement)
  
- **Acceptance Criteria**:
  - Logs cannot be tampered with or deleted
  - Log search and analysis tools
  - Automated log anomaly detection
  - Security Information and Event Management (SIEM) integration
  - Regular log reviews
  - Alerts for suspicious activities

**REQ-SEC-005: API Security**
- **API Authentication**:
  - OAuth 2.0 / OpenID Connect
  - API keys for service accounts
  - JWT tokens for session-based access
  
- **API Authorization**:
  - Scope-based permissions
  - Rate limiting per API key/user
  - IP whitelisting (optional, for sensitive APIs)
  
- **API Input Validation**:
  - Request schema validation (JSON Schema)
  - Parameter sanitization
  - SQL injection prevention
  - Maximum payload size (10MB default)
  
- **API Security Headers**:
  - Strict-Transport-Security
  - Content-Security-Policy
  - X-Content-Type-Options
  - X-Frame-Options
  - Referrer-Policy
  
- **Acceptance Criteria**:
  - API documentation with security considerations
  - API versioning (to deprecate insecure endpoints)
  - API abuse detection and blocking
  - API security testing (OWASP API Top 10)

**REQ-SEC-006: File Upload Security**
- **File Validation**:
  - File extension whitelist
  - MIME type validation
  - Magic byte validation (file signature)
  - File size limits (configurable per file type)
  - Filename sanitization (remove special characters)
  
- **Malware Scanning**:
  - Antivirus scanning on upload (ClamAV or commercial solution)
  - Quarantine suspicious files
  - Sandboxed file processing
  
- **File Storage Security**:
  - Separate storage domain (no script execution)
  - Unique file identifiers (not user-controlled filenames)
  - Prevent directory traversal
  - Access control on file downloads
  
- **Acceptance Criteria**:
  - 100% of files scanned before making available
  - Infected files rejected with notification
  - File metadata stripped (EXIF, document properties)
  - File preview in sandboxed viewer

**REQ-SEC-007: Dependency Management**
- **Acceptance Criteria**:
  - Automated dependency scanning (Snyk, Dependabot, npm audit)
  - Regular dependency updates (weekly review)
  - Vulnerability alerting
  - Patch management process
  - Software Bill of Materials (SBOM) generation
  - License compliance checking

**REQ-SEC-008: Secure Development Lifecycle**
- **Security Activities**:
  - Threat modeling for new features
  - Security code reviews
  - Static Application Security Testing (SAST)
  - Dynamic Application Security Testing (DAST)
  - Interactive Application Security Testing (IAST)
  - Penetration testing (annually)
  - Security training for developers
  
- **Acceptance Criteria**:
  - Security review required before production deployment
  - Security checklist for each release
  - Security gates in CI/CD pipeline
  - Incident response plan documented and tested

### Compliance Requirements

**REQ-COMP-001: GDPR Compliance**
- **Data Protection Principles**:
  - Lawfulness, fairness, and transparency
  - Purpose limitation
  - Data minimization
  - Accuracy
  - Storage limitation
  - Integrity and confidentiality
  - Accountability
  
- **Implementation Requirements**:
  - **Consent Management**:
    - Explicit consent for data processing
    - Granular consent options
    - Consent withdrawal mechanism
    - Consent audit trail
  
  - **Data Subject Rights**:
    - Right to access (data export)
    - Right to rectification (self-service data correction)
    - Right to erasure ("right to be forgotten")
    - Right to restriction of processing
    - Right to data portability (export in machine-readable format)
    - Right to object
    - Rights related to automated decision-making
  
  - **Data Protection Impact Assessment (DPIA)**:
    - DPIA for high-risk processing
    - Document data flows
    - Risk mitigation measures
  
  - **Data Breach Notification**:
    - Detect breaches within 24 hours
    - Notify supervisory authority within 72 hours
    - Notify affected individuals if high risk
    - Breach register
  
  - **Data Retention & Deletion**:
    - Retention policies per data type
    - Automatic deletion after retention period
    - Secure deletion (cryptographic erasure)
    - Audit log retention (7 years for financial compliance)
  
- **Acceptance Criteria**:
  - Privacy Policy published and accessible
  - Cookie consent banner
  - Data Protection Officer (DPO) contact information
  - Privacy by Design and by Default
  - Regular GDPR audits
  - GDPR training for staff

**REQ-COMP-002: Financial Sector Regulations**
- **Regulatory Frameworks**:
  - Polish Banking Law
  - Polish Insurance and Reinsurance Activity Act
  - Capital Requirements Regulation (CRR)
  - Markets in Financial Instruments Directive (MiFID II)
  - Payment Services Directive (PSD2)
  - Anti-Money Laundering (AML) / Know Your Customer (KYC)
  
- **Compliance Requirements**:
  - **Data Retention**: Minimum 7 years for financial records
  - **Audit Trail**: Complete, immutable audit logs
  - **Segregation of Duties**: Enforce SoD policies
  - **Change Management**: Documented change approval process
  - **Business Continuity**: Disaster recovery and backup plans
  - **Incident Reporting**: Report security incidents to regulator
  
- **Acceptance Criteria**:
  - Compliance mapping documentation
  - Regular compliance audits
  - Compliance officer assigned
  - Regulatory reporting capabilities

**REQ-COMP-003: Data Residency & Sovereignty**
- **Acceptance Criteria**:
  - All data stored in Poland or EU
  - Data center certifications (ISO 27001, SOC 2)
  - No cross-border data transfers outside EU (without adequacy decision)
  - Cloud provider compliance (if using cloud infrastructure)
  - Contractual data processing agreements

**REQ-COMP-004: Accessibility Compliance (see dedicated section)**

---

## Accessibility Requirements (WCAG 2.1 AA)

### Overview
The platform must comply with **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA** to ensure equal access for all users, including those with disabilities.

### Perceivable

**REQ-ACCESS-001: Text Alternatives**
- **Acceptance Criteria**:
  - All images have descriptive alt text
  - Decorative images have empty alt attribute (alt="")
  - Icons have aria-labels or visually hidden text
  - Complex images have long descriptions
  - CAPTCHAs have alternative formats (audio CAPTCHA)

**REQ-ACCESS-002: Time-based Media**
- **Acceptance Criteria**:
  - Videos have captions/subtitles
  - Videos have audio descriptions (if relevant)
  - Transcripts provided for audio content
  - Auto-playing media can be paused

