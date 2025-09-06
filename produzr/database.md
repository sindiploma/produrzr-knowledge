# Database

# Database Schema Documentation

This document describes the data structure that powers Produzr’s production management platform.

## Core Architecture

Produzr’s database is built around three fundamental pillars:
- **People** (Who is involved)
- **Events** (What happens when)

- **Services** (How things get done)

## Data Models

### Tenant (Multi-Company Support)

Organizations using Produzr. Each tenant can manage multiple projects.

**Fields:**
- `name` - Company or organization name

**Relationships:**
- Has many `Projects`

---

### Project (Production Management)

Individual productions being managed within a tenant.

**Fields:**
- `name` - Project title or code name

**Relationships:**
- Belongs to one `Tenant`
- Has many `ProjectRoles`
- Has many `ProjectEvents`
- Has many `ProjectServices`

---

### Person (People Database)

Individual people who participate in productions.

**Fields:**
- `firstName` - Given name
- `lastName` - Family name

- `email` - Contact email (unique across system)

**Relationships:**
- Can have multiple `ProjectRolePerson` assignments

---

### Department (Organizational Structure)

Groups roles by function and type within productions.

**Categories:**
- `CREW` - Technical and creative staff
- `CLIENT` - Agency and brand representatives
- `TALENT` - On-screen performers
- `SUPPLIER` - Equipment and service providers
- `OTHER` - Miscellaneous roles

**Fields:**
- `category` - One of the above categories
- `name` - Department name (e.g., “Camera”, “Sound”, “Wardrobe”)

**Relationships:**
- Has many `ProjectRoles`

---

### ProjectRole (Job Functions)

Specific positions needed within a project, organized by department.

**Fields:**
- `name` - Role title (e.g., “Director of Photography”, “Gaffer”)

**Relationships:**
- Belongs to one `Department`
- Belongs to one `Project`
- Can have multiple `ProjectRolePerson` assignments
- Has many `ProjectRoleNeeds` for logistics

---

### ProjectRolePerson (Assignment Bridge)

Links people to specific roles within projects (many-to-many relationship).

**Relationships:**
- Links one `Person` to one `ProjectRole`

---

### ProjectRoleNeeds (Logistics Requirements)

Defines what each role needs for specific dates during production.

**Fields:**
- `name` - Description of the need
- `date` - When this is needed
- `walkies` - Requires walkie-talkie communication
- `catering` - Requires meal service
- `transport` - Requires transportation

**Relationships:**
- Belongs to one `ProjectRole`

---

### ProjectEvent (Timeline Management)

Activities and milestones within a production timeline.

**Types:**
- `SHOOT` - Filming/recording sessions
- `PICKUP` - Additional footage capture
- `MEAL` - Catering events
- `ACCOMMODATION` - Lodging arrangements
- `OTHER` - Miscellaneous events

**Fields:**
- `type` - One of the above event types
- `name` - Event description

**Relationships:**
- Belongs to one `Project`
- Can use one `ProjectService` for transport

---

### Supplier (Vendor Management)

External companies providing services to productions.

**Fields:**
- `contactPersonName` - Primary contact name
- `contactPersonEmail` - Contact email
- `contactPersonPhone` - Phone number (optional)
- `contactPersonRole` - Contact’s job title (optional)

**Relationships:**
- Provides many `ProjectServices`

---

### ProjectService (Service Management)

Services provided by suppliers for projects.

**Types:**
- `TRANSPORT` - Vehicle and logistics services
- `CATERING` - Food and beverage services

**Fields:**
- `type` - Service category
- `name` - Service name
- `description` - Service details (optional)
- `price` - Service cost

**Relationships:**
- Belongs to one `Project`
- Provided by one `Supplier` (optional)
- Can be used by multiple `ProjectEvents`

---

## Key Relationships

### Multi-Tenancy

```plain text
Tenant → Projects → (Roles, Events, Services)
```

### People Assignment

```plain text
Person → ProjectRolePerson → ProjectRole → Department
```

### Event Planning

```plain text
ProjectEvent → ProjectService → Supplier
```

### Logistics Coordination

```plain text
ProjectRole → ProjectRoleNeeds (walkies, catering, transport)
```

## Data Flow Examples

### Adding a New Crew Member

1. Create or find `Person` record
1. Create `ProjectRole` under appropriate `Department`
1. Link via `ProjectRolePerson`
1. Define `ProjectRoleNeeds` for logistics
### Planning a Shoot Day

1. Create `ProjectEvent` of type `SHOOT`
1. Assign `ProjectService` for transport if needed
1. Check `ProjectRoleNeeds` for catering requirements
1. Generate documentation from consolidated data
### Managing Suppliers

1. Create `Supplier` with contact information
1. Define `ProjectServices` they provide
1. Link services to `ProjectEvents` as needed
1. Track costs and logistics coordination
## System Benefits

**Data Consistency:** Single source of truth for all production information

**Cross-Reference Capability:** Any data point can reference others (people in events, services for roles, etc.)

**Automated Documentation:** All reports generated from this centralized data

**Multi-Project Scaling:** Same people and suppliers can work across different projects within a tenant

# Entity Relationship Diagram

[Unsupported block type: bookmark]

