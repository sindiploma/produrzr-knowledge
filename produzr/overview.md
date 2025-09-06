# Overview

## Executive Summary

Our platform is a comprehensive production management solution designed specifically for commercial, fashion, and music video audiovisual productions. It streamlines the complex logistics of these high-intensity productions by managing people, schedules, and locations while automatically generating all necessary documentation to keep teams informed and coordinated.

The platform addresses the critical challenge of production coordination by centralizing information and automating documentation workflows, enabling producers to focus on creative execution rather than administrative overhead.

## Current Product Capabilities

### Platform Architecture

The platform is built on three foundational pillars that enable comprehensive data cross-referencing and dashboard creation:

- **People (Who)**: Comprehensive management of all production stakeholders
- **Events (What)**: Timeline management of all production activities
- **Locations (Where)**: Geographic coordination of shooting and logistics sites
This architecture creates a unified timeline of all activities that comprise an audiovisual production, currently focused on the production phase (shooting), with future expansion planned for pre-production and post-production phases.

### Platform Structure

The application is organized around project-based navigation, with all production management tools nested within individual projects:

**Project Management:**

- `/projects`
- `/projects/{projectName}`
**Organizational Structure:**

- `/departments`
**Core Management Pages (within each project):**

- `/projects/{projectName}/people` (with drawer navigation: `#person-name-tab`)
- `/projects/{projectName}/people/add` (dedicated add person page)
- `/projects/{projectName}/events`
- `/projects/{projectName}/events/add` (dedicated add event page)
- `/projects/{projectName}/locations`
- `/projects/{projectName}/locations/add` (dedicated add location page)
**Document Generation (within each project):**

- `/projects/{projectName}/documents`
- `/projects/{projectName}/documents/talent` (with `/edit` mode available)
- `/projects/{projectName}/documents/locations` (with `/edit` mode available)
- `/projects/{projectName}/documents/walkie` (with `/edit` mode available)
- `/projects/{projectName}/documents/catering` (with `/edit` mode available)
- `/projects/{projectName}/documents/rooming` (with `/edit` mode available)
- `/projects/{projectName}/documents/transport` (with `/edit` mode available)
- `/projects/{projectName}/documents/schedule` (with `/edit` mode available)
- `/projects/{projectName}/documents/arrivals-departures` (with `/edit` mode available)
- `/projects/{projectName}/documents/crew` (with `/edit` mode available)
- `/projects/{projectName}/documents/vans` (with `/edit` mode available)
- `/projects/{projectName}/documents/altas` (with `/edit` mode available)
**User Management:**

- `/team`
- `/invites`
**Settings:**

- `/settings/account`
- `/settings/profile`
- `/settings/organization`
### User Permission Matrix

**Role-Based Access Control**

[Table content - 6 columns]

| Role | Create Projects | Edit People | Modify Events | Generate Docs | Admin Settings |
| Executive Producer | ✅ | ✅ | ✅ | ✅ | ✅ |
| Producer | ✅ | ✅ | ✅ | ✅ | ❌ |
| Production Manager | ❌ | ✅ | ✅ | ✅ | ❌ |
| Coordinator | ❌ | ✅ | ✅ | ✅ | ❌ |
| Production Assistant | ❌ | ✅ | ❌ | ✅ | ❌ |
*Permissions align with industry hierarchy and production workflow responsibilities.*

### People Management

The People module maintains a comprehensive database of all individuals connected to a production, including:

- **Crew members**: Technical and creative staff
- **Clients**: Agency and brand representatives
- **Talent**: On-screen performers
- **Vendors**: Equipment and service providers
Each person profile contains:

- Personal and contact information
- Billing and invoicing details
- Dietary restrictions and allergies
- Production-specific logistics (catering participation, walkie-talkie assignment, etc.)
### Event Management

The Events module tracks all production activities including:

- Prep days and pre-production meetings (PPM)
- Technical reconnaissance (Tech Recce)
- Wardrobe fittings
- Shooting days
- Arrival and departure coordination for visiting crew
### Location Management

An interactive map-based interface that consolidates:

- Primary shooting locations
- Accommodation facilities for visiting crew
- Dining venues for client entertainment
- Transportation logistics points
### Automated Documentation Generation

The platform automatically generates essential production documents:

- **Talent sheets**: Cast information and requirements
- **Location guides**: Site details and logistics
- **Walkie-talkie assignments**: Communication protocols
- **Catering lists**: Meal planning and dietary accommodations
- **Rooming charts**: Accommodation assignments
- **Transport orders**: Vehicle and logistics coordination
- **Production schedules**: Comprehensive timeline management
- **Arrivals & Departures**: Travel coordination for visiting crew
- **Crew lists**: Complete team rosters
- **Runner assignments**: Transportation and logistics support
- **Payroll documentation**: Administrative processing support
### Real-Time Synchronization & Business Rules

**Change Propagation Logic**

When data is updated in one area, the system automatically:

1. **Identifies Dependencies**: Scans which documents reference the changed data
1. **Updates Documents**: Regenerates affected documents with new information
1. **Notifies Stakeholders**: Alerts relevant team members of changes
1. **Maintains Version History**: Preserves previous versions for reference
**Example Workflow**: When a shooting location changes:

- Location sheets update with new address/details
- Transport orders recalculate routes and timing
- Catering arrangements adjust for new venue requirements
- Team notifications sent about location change
**Data Integrity Rules**

- People must have minimum contact information before appearing in documents
- Events cannot overlap conflictingly for same resources
