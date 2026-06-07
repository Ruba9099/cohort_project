# Project Constitution

## Web Application

## Tech Stack Constraints

- Frontend Framework: Next.js 15 or later.
- Styling: No inline styles or external UI component libraries without prior team approval.
- Backend / API: Use Next.js Server Actions or a dedicated FastAPI Python backend.
- Database: Use PostgreSQL through Prisma ORM. Raw SQL is allowed only in explicit migrations.test

## Architecture Principles

- Component Modularity: Every feature must be organized as a standalone module with clear ownership.
- State Management: Server Components should be the default. React Context should only be used when state must be shared across multiple unrelated components.
- Error Handling: All asynchronous operations must use consistent error handling, logging, and user-facing failure messages where applicable.
- API Boundaries: API routes and server actions must have clearly defined request validation, response formats, and authorization checks.

## Code Quality and Testing Standards

- Every sprint must be tested properly before a pull request is accepted.
- Naming Conventions:
  - Components: `PascalCase`
  - Utilities and Hooks: `camelCase`
- Code Formatting: The project Prettier configuration is the standard. Code must be formatted before commit.
- Documentation: Important features, setup steps, API behavior, and architectural decisions must be documented.
- Pull Requests: Pull requests must include a clear summary, testing notes, and any known risks or limitations.

## Governance Structure

- Steering Committee: Responsible for strategic direction, approvals, and major decisions.
- Project Manager: Responsible for planning, execution, monitoring, and reporting.
- Development Team: Responsible for system design, coding, testing, and deployment.
- Quality Assurance Team: Responsible for testing, validation, and quality compliance.
- Stakeholders: Responsible for providing business requirements, feedback, and acceptance.

## Roles and Responsibilities

- Sponsor: Provides funding approvals and strategic guidance.
- Project Manager: Coordinates project planning, delivery, communication, and tracking.
- Business Analyst: Gathers, analyzes, and documents requirements.
- UI/UX Designer: Designs the user experience and interface.
- Developers: Build, maintain, and document the application.
- QA Engineers: Test features, report defects, and verify quality standards.
- Product Owner: Prioritizes features and confirms acceptance criteria.

## Constitutional Laws

### Negotiable Laws

The following may be adapted depending on the scenario, with proper justification and approval:

- Project success criteria.
- Technology constraints.
- Code naming conventions.
- Development tools.
- Sprint planning and delivery approach.

### Non-Negotiable Laws

- Security is the main priority, and there will be no compromise on security.
- All important project details must be documented.
- Every meaningful chunk of code must be tested before integration with the main system.
- Stakeholders or clients must be updated continuously.
- No requirement changes may be made without client approval.
- Ambiguous or unclear requirements must be discussed with the client instead of being skipped or assumed.

## Change Management

Any change to scope, budget, timeline, or major requirements must:

- Be documented.
- Be reviewed by stakeholders.
- Receive appropriate approval.
- Be communicated to all affected parties.

## Communication Plan

Project communications shall include:

- Weekly status meetings.
- Sprint reviews and demonstrations.
- Progress reports.
- Risk and issue reporting.
- Stakeholder feedback sessions.

## Success Criteria

The project will be considered successful when:

- All approved requirements are delivered.
- System performance targets are achieved.
- Security requirements are met.
- Stakeholders formally approve the solution.
- The application is successfully deployed and operational.
