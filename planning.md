# Planning: Student To-Do App

> **How to read this document**
> Everything here comes from decisions the team stated. Items marked **⚠ To confirm** were not explicitly decided, so they are written as a mechanical reading of your decisions and need a yes/no from you. Items marked **❓ Open** are undecided and are collected in the Open Decisions section at the end.

---

## 1. Overview

| | |
|---|---|
| **Project name** | ❓ Open (not yet named) |
| **Type** | Website (full stack) |
| **Audience** | Students |
| **Unique feature** | Automated daily email reminders |
| **Release target** | Production ready: deployed and publicly accessible |
| **Deadline** | 1 week for the whole project |

## 2. Problem Statement

Students miss assignments. This app helps students keep track of their tasks and assignments, and it reminds them automatically every day until each task is done.

The app tracks **tasks and assignments**. It does not manage class timetables or schedules.

## 3. Target Users

- **Students only.** There are no other user types (no teachers, no admins).
- Each user can only see and manage **their own** tasks.

## 4. User Requirements

As a student, I want to:

| # | Requirement |
|---|---|
| U1 | Sign up with my email, name and password |
| U2 | Verify my email address through a link sent to me (the link lasts 5 minutes) |
| U3 | Log in (only after I have verified my email) and log out |
| U4 | Reset my password if I forget it |
| U5 | Create a task with a title, description, priority, due date, and reminder settings |
| U6 | Have my task inputs checked so I get clear feedback when something is invalid |
| U7 | Save my task so it is still there when I come back |
| U8 | Edit a task |
| U9 | Delete a task |
| U10 | Mark a task as complete |
| U11 | Filter my tasks to show **All**, **Completed** or **Uncompleted** |
| U12 | Turn on a reminder for a task and choose the date reminders start |
| U13 | Receive an email reminder every day at 6 AM, starting on the reminder start date, until I complete the task |
| U14 | Use the app comfortably on my phone |

## 5. Functional Requirements (MVP)

### 5.1 Accounts and authentication
- Sign up with **email, name and password**.
- Standard password rules apply (❓ exact rules are open, see Open Decisions).
- **Email verification** is required. A verification email is sent at sign-up, and the link expires after **5 minutes**.
- **Unverified users are blocked from logging in** until they verify.
- **Login and logout.**
- **Password reset** by email.
- **Session-based authentication.** The browser receives a session cookie at login and sends it with every request to the server.
- Users can only access their own data.

### 5.2 Task management
- **Create task:** builds a new task with all necessary fields and validates the inputs.
- **Save task:** persists the task to the database.
- **Edit task.**
- **Delete task.**
- **Mark task complete.**
- **Filter tasks:** All, Completed, Uncompleted.

### 5.3 Task fields

| Field | Rules |
|---|---|
| Task ID | Unique identifier |
| Task title | Required |
| Description | Text |
| Priority | Fixed set: **low, medium, high** |
| Due date | **Date is required; time is optional** |
| Remind me | Yes/no toggle |
| Reminder start date | The date the daily reminders begin (used when Remind me is yes) |
| Completed | Yes/no; new tasks start as not completed |

### 5.4 Reminders (the unique feature)
- Delivered by **email**, sent through the **Brevo API** (free tier).
- Sent at **6 AM every day**, starting on the task's **reminder start date**.
- Repeats **every day until the task is marked completed**.
- Only applies to tasks where Remind me is yes.
- The mechanism that triggers the reminders on schedule is ❓ undecided.

### 5.5 Emails sent by the system
Brevo API is used for all of these:
1. Email verification
2. Password reset
3. Task reminders

## 6. Non-Functional Requirements

- **Mobile-friendly:** the app must be highly mobile-friendly.
- **User-friendly:** clear, simple flows and clear error messages.
- **Production ready:** deployed, publicly accessible, with tests and error handling.
- **Security:** each user's data is private to them (see 5.1).

## 7. Scope and Boundaries

**In scope:** everything in the MVP list above.

**The team has stated that nothing is explicitly out of scope.** The following were decided as *not part of this version*:

- Class timetables or schedules (only tasks and assignments)
- Other user types beyond students
- Timezone handling
- Sorting and searching tasks (only the completed-status filter exists)
- Categories, courses or tags
- Voice input (see Future)

## 8. MVP vs Future

### MVP
1. Sign up, login, logout
2. Email verification
3. Password reset
4. Create task (with input validation)
5. Save task
6. Edit task
7. Delete task
8. Mark task complete
9. Filter tasks (All / Completed / Uncompleted)
10. Automated daily email reminders

### Future
- **Voice input**

## 9. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | HTML5, TailwindCSS, Vanilla JavaScript |
| Frontend hosting | Vercel |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Backend hosting | Render |
| Email service | Brevo API (free tier) |
| Authentication | Session-based (session cookie) |
| Backend testing | pytest |
| Frontend quality | Linting (❓ specific linter not chosen) |
| Version control | Git and GitHub, one repository containing both the frontend and backend |
| Database migrations | ❓ Open |
| CI | ❓ Open |

The frontend and backend are **hosted separately**.

## 10. Team and Roles

| Role | Person |
|---|---|
| Frontend developer | Mac Ty |
| Backend developer | Maurice123-Tech |

The frontend and backend are connected from the very first milestone, and each milestone is tested end to end before the team moves on.

## 11. Timeline

**1 week for the whole project.** The milestone plan and a suggested day-by-day pacing are in `architecture.md`, section 6.

## 12. Success Metrics (draft)

**⚠ To confirm.** You asked for a success metrics section but did not give metrics. These are drawn only from your stated requirements. Edit freely.

| # | Metric | How to check |
|---|---|---|
| S1 | A new user can complete the full journey on the deployed site: sign up, verify email, log in, create a task with a reminder | Manual end-to-end test on the live Vercel and Render URLs |
| S2 | Unverified users cannot log in | Backend test plus manual check |
| S3 | A user can never read, edit, complete or delete another user's task | Backend tests (pytest) |
| S4 | A task with Remind me on produces an email at 6 AM on its reminder start date and every day after | Live test using a task whose start date is today or tomorrow |
| S5 | Reminder emails stop once the task is marked complete | Live test the day after completing a task |
| S6 | Every MVP feature works at phone screen width | Manual test on a real phone |
| S7 | Backend tests pass and the frontend linter is clean | Run pytest and the linter before every merge |
| S8 | All MVP features are delivered within the 1-week deadline | Final demo |

## 13. Risks (draft)

**⚠ To confirm.** Drawn only from your decisions. Edit freely.

| # | Risk | Why it matters |
|---|---|---|
| R1 | **Tight deadline.** The MVP includes auth with email verification, password reset, full task CRUD, filtering and scheduled reminders, all in 1 week | Little room for rework; the milestone order should protect the core features first |
| R2 | **Reminder trigger is undecided** | The reminder feature, your unique feature, cannot be finished until this is chosen |
| R3 | **Cross-domain session cookie.** Frontend (Vercel) and backend (Render) are on different domains, and auth relies on a session cookie | Cookies across separate domains can be blocked or dropped by browsers. Test this early, not at the end |
| R4 | **Brevo free tier.** All emails go through it | Check the free-tier sending limits and whether emails land in spam |
| R5 | **5-minute verification link** | A user who misses the window may be stuck if there is no way to request a new link (❓ open) |
| R6 | **6 AM with no timezone handling** | It must be decided which clock "6 AM" refers to (❓ open) |
| R7 | **Hosting plan behaviour.** Free tiers of some hosts may pause idle services | A paused backend could miss the 6 AM reminder run. Check your plans |
| R8 | **Frontend and backend drifting apart** | Mitigation: treat the API contract in `architecture.md` as the shared source of truth and update it before changing an endpoint |

## 14. Open Decisions (product)

These need an answer from the team. Architecture-related open decisions are listed in `architecture.md`, section 7.

| # | Question |
|---|---|
| P1 | What is the project name? |
| P2 | 6 AM in which timezone (server time, UTC, or another)? You said no timezone handling, so this needs a single fixed answer. |
| P3 | Reminders continue every day until completed, even after the due date has passed. Is that correct? |
| P4 | Can the reminder start date be after the due date? Can it be in the past when the task is created? |
| P5 | Can a completed task be marked as not completed again? |
| P6 | What exactly are the "standard" password rules (minimum length, required characters)? |
| P7 | How long does a password reset link last? How long does a login session last? |
| P8 | Can a user request a new verification email if their link expired? |
| P9 | What happens if a reminder email fails to send (retry, skip, log)? |
| P10 | What does the reminder email say (subject and content)? |
| P11 | Limits on fields (maximum title length, maximum description length)? |
| P12 | In what order is the task list shown by default (for example by due date or newest first), given there is no sorting feature? |
| P13 | Which frontend linter will you use? |
| P14 | Branching workflow in GitHub (for example feature branches and pull requests, or work on main)? |
| P15 | Will you set up CI (for example GitHub Actions)? |
