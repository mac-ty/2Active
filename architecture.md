# Architecture: Student To-Do App

> **How to read this document**
> This is written only from the team's stated decisions. Where an endpoint path, column or behaviour had to be written down but was not decided by you, it is marked **⚠ To confirm**. Undecided items are marked **❓ Open** and collected in section 7. This file is the shared source of truth between frontend and backend: update it **before** changing an endpoint.

---

## 1. High-Level Architecture

```
┌──────────────────────┐        HTTPS + session cookie        ┌──────────────────────────┐
│  Frontend            │ ───────────────────────────────────► │  Backend                 │
│  HTML5, Tailwind,    │ ◄─────────────────────────────────── │  Python, FastAPI         │
│  Vanilla JS          │            JSON responses            │  SQLAlchemy              │
│  Hosted on Vercel    │                                      │  Hosted on Render        │
└──────────────────────┘                                      └───────┬──────────┬───────┘
                                                                      │          │
                                                          SQL queries │          │ HTTPS API calls
                                                                      ▼          ▼
                                                             ┌──────────────┐  ┌─────────────┐
                                                             │ PostgreSQL   │  │ Brevo API   │
                                                             │ database     │  │ (email)     │
                                                             └──────────────┘  └─────────────┘
                                                                      ▲
                                                                      │ reads due reminders
                                                             ┌────────┴─────────────┐
                                                             │ Reminder trigger     │
                                                             │ daily at 6 AM        │
                                                             │ ❓ mechanism open    │
                                                             └──────────────────────┘
```

### 1.1 Components

| Component | Responsibility |
|---|---|
| **Frontend (Vercel)** | Pages for sign up, login, email verification code entry, password reset, and task management. Sends requests to the backend and shows results. Mobile-first layout. |
| **Backend (Render)** | Authentication and sessions, input validation, task logic, email sending, and database access. Enforces that users only touch their own tasks. |
| **PostgreSQL** | Stores users, tasks and the codes used for verification and password reset. |
| **Brevo API** | Sends verification emails, password reset emails and task reminder emails. |
| **Reminder trigger** | Runs every day at 6 AM and sends reminder emails for tasks that qualify (see 1.3). ❓ The mechanism is undecided. |

### 1.2 Key flows

**Sign up and verify**
1. User submits name, email and password.
2. Backend validates, stores the user as unverified, and sends a verification email with a 6-digit code through Brevo.
3. User enters the 6-digit code from the email within 5 minutes.
4. Backend marks the user as verified.

**Login and session**
1. User submits email and password.
2. Backend rejects the login if the user is not verified.
3. Otherwise the backend creates a session and returns a session cookie.
4. The browser sends that cookie on every later request, and the backend uses it to identify the user.

**Create and save a task**
1. Frontend sends the task fields.
2. Backend validates every input (the "create" step).
3. Backend writes the task to the database (the "save" step) and returns the saved task.

**Daily reminders**
1. At 6 AM each day the trigger runs.
2. The backend finds every task where Remind me is yes, the task is not completed, and the reminder start date has been reached (today or earlier).
3. For each one, it sends a reminder email to the task's owner through Brevo.
4. Completed tasks stop appearing in this list, so their reminders stop.

### 1.3 Cross-origin note

The frontend and backend live on different domains and auth uses a session cookie. The backend must accept requests from the Vercel origin **with credentials**, and the frontend must send credentials on every request. Cookie settings that make this work across domains are ❓ open (see section 7).

### 1.4 Repository

One GitHub repository contains both projects, in two folders at the root: backend/ and frontend/.

---

## 2. Data Models

### 2.1 `users`

| Column | Type | Rules |
|---|---|---|
| `id` | UUID  | Primary key |
| `name` | string | Required |
| `email` | string | Required, **unique** |
| `password_hash` | string | Required. Passwords are never stored in plain text |
| `is_verified` | boolean | Default `false`. Set to true when the verification code is accepted.|
| `created_at` | timestamp | Set on creation |

### 2.2 `tasks`

| Column | Type | Rules |
|---|---|---|
| `task_id` | UUID | Primary key |
| `user_id` | same type as `users.id` | Required, foreign key to `users.id`. Every query filters by this |
| `task_title` | string | Required |
| `description` | text | Optional ⚠ |
| `priority` | enum | One of `low`, `medium`, `high`. Required ⚠ |
| `due_date` | date | **Required** |
| `due_time` | time | **Optional** ⚠ (stored separately from the date) |
| `remind_me` | boolean | Yes/no toggle. Default `false` ⚠ |
| `reminder_start_date` | date | Required when `remind_me` is `true`; otherwise empty ⚠ |
| `completed` | boolean | Default `false` |
| `created_at` | timestamp | Set on creation ⚠ |
| `updated_at` | timestamp | Updated on every edit ⚠ |

### 2.3 Email codes (verification and password reset)

Both flows use a 6-digit code sent by email, which proves the person owns the email address.

| Column | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Required, foreign key to `users.id` |
| `code_hash` | string | The 6-digit code, stored hashed. Never stored in plain text |
| `purpose` | enum | `verify_email` or `reset_password` |
| `expires_at` | timestamp | Verification: 5 minutes after creation. Reset: 10 minutes after creation|
| `used` | boolean | Default `false`. A code can only be used once |
| `failed_attempts` | integer | Default `0`. After 5 wrong attempts the code stops working |
| `created_at` | timestamp | Set on creation. Used for the 60-second wait between requests |

**Rules**
- The code is exactly 6 digits.
- A code is looked up by the user's email and its purpose, not by the code alone, because 6-digit codes are not unique across users.
- A new code replaces the old one: any earlier unused code for the same user and purpose stops working.
- A user must wait 60 seconds between code requests for the same purpose.
- After 5 wrong attempts the code is invalidated and the user must request a new one.

### 2.4 Sessions

Session-based auth is decided. **Where session data is stored** (a database table, memory, or elsewhere) is ❓ open. When decided, add the table or description here.

### 2.5 Relationships

- One user has many tasks (`tasks.user_id` → `users.id`).
- One user has many email codes (`email_codes.user_id` → `users.id`).
- Deleting a task removes it permanently. What happens to a user's tasks if a user is removed is ❓ not decided (account deletion is not in the MVP).

### 2.6 Validation rules (the "create task" step)

| Field | Rule |
|---|---|
| `task_title` | Required, not blank. ❓ Max length |
| `description` | Optional. ❓ Max length |
| `priority` | Must be `low`, `medium` or `high` |
| `due_date` | Required and must be a valid date |
| `due_time` | Optional, but if present must be a valid time |
| `remind_me` | Must be true or false |
| `reminder_start_date` | Required if `remind_me` is true and must be a valid date. ❓ Relationship to `due_date` and to today is open |

---

## 3. API Contracts

**⚠ To confirm.** You decided the features, not the URLs, so the paths below are a literal reading of those features. Rename anything you like, but agree on it together and update this file.

**General rules**
- All request and response bodies are JSON.
- Base URL: http://127.0.0.1:8000 locally, and https://student-todo-api.onrender.com in production.
- **Session cookie:** set by `POST /auth/login`. The frontend sends it on every request (credentials included).
- All `/tasks` endpoints require a valid session. Without one the response is `401`.
- Error body: a JSON object with a `detail` field describing the problem (FastAPI's default format) ⚠.

### 3.1 Auth endpoints

#### `POST /auth/signup`
Create an account and send the verification email.

Request:
```json
{ "name": "Ama Mensah", "email": "ama@example.com", "password": "..." }
```
Responses:
- `201` account created, verification email sent
- `409` email already registered
- `422` invalid input (blank name, bad email, password breaks the rules)

#### `POST /auth/verify-email`
Verify an email address using the 6-digit code sent to it.

Request:
```json
{ "email": "ama@example.com", "code": "123456" }
```
Responses:
- `200` email verified
- `400` code is wrong, already used, expired (older than 5 minutes), or has been invalidated after 5 wrong attempts. The message is the same in every case, so it does not reveal whether the email has an account
- `422` invalid input (bad email format, code is not exactly 6 digits)

#### `POST /auth/resend-verification`
Sends a new verification code. Any earlier unused code stops working.

Request: `{ "email": "ama@example.com" }`
- `200` always returns the same message, whether or not the email has an account or is already verified. If a code was requested less than 60 seconds ago, no new code is sent and the response is still this same `200`
- `422` invalid email format



#### `POST /auth/login`
Request:
```json
{ "email": "ama@example.com", "password": "..." }
```
Responses:
- `200` login successful, session cookie set, returns the user (`id`, `name`, `email`)
- `401` wrong email or password
- `403` email not verified yet

#### `POST /auth/logout`
Ends the session and clears the cookie.
- `204` done

#### `POST /auth/forgot-password`
Sends a 6-digit password reset code to the email if an account exists. Any earlier unused reset code stops working.

Request: `{ "email": "ama@example.com" }`
- `200` always returns the same message, whether or not the email has an account. If a code was requested less than 60 seconds ago, no new code is sent and the response is still this same `200`
- `422` invalid email format

#### `POST /auth/reset-password`
Sets a new password using the code from the email.

Request: `{ "email": "ama@example.com", "code": "123456", "new_password": "..." }`
- `200` password changed
- `400` code is wrong, already used, expired (older than 10 minutes), or invalidated after 5 wrong attempts. The message is the same in every case
- `422` invalid input (code is not exactly 6 digits, or the new password breaks the rules: 8 to 64 characters with at least one letter and one number)

#### `GET /auth/me` ⚠
Lets the frontend ask "who is logged in?" when a page loads.
- `200` returns `{ "id", "name", "email" }`
- `401` not logged in

### 3.2 Task endpoints (all require a session)

**Task object** returned by the API:
```json
{
  "task_id":  "3f2b8c1e-5a47-4d9e-8b21-7c6d0e4a9f15",
  "task_title": "Submit data structures assignment",
  "description": "Chapters 4 and 5",
  "priority": "high",
  "due_date": "2026-11-20",
  "due_time": "17:00",
  "remind_me": true,
  "reminder_start_date": "2026-11-17",
  "completed": false
}
```
`due_time` is `null` when no time was given. `reminder_start_date` is `null` when `remind_me` is `false`.

#### `POST /tasks`
Validates the inputs (create) and saves the task to the database (save). ⚠ This is written as one request. If you want the two steps to be separate calls, say so.

Request body: `task_title`, `description`, `priority`, `due_date`, `due_time` (optional), `remind_me`, `reminder_start_date`.
- `201` returns the saved task object
- `401` not logged in
- `422` validation error (details say which field)

#### `GET /tasks?status=all|completed|uncompleted`
Returns only the logged-in user's tasks, filtered by completion.
- `status` is optional and defaults to `all` ⚠
- `200` returns a list of task objects
- `401` not logged in
- `422` invalid `status` value

#### `GET /tasks/{task_id}` ⚠
Returns one task, so the edit form can be filled in.
- `200` task object
- `404` task does not exist or does not belong to this user ⚠

#### `PUT /tasks/{task_id}` ⚠
Edit a task. Sends the same fields as create. Same validation rules.
- `200` returns the updated task
- `404` not found or not yours
- `422` validation error

#### `PATCH /tasks/{task_id}/complete` ⚠
Marks the task as completed. This stops its reminders.
- `200` returns the updated task
- `404` not found or not yours

❓ Whether a task can be un-completed is open.

#### `DELETE /tasks/{task_id}`
- `204` deleted
- `404` not found or not yours

### 3.3 Reminder job contract

Not an HTTP endpoint (❓ how it is triggered is open). When it runs at 6 AM:

- **Selects** tasks where `remind_me = true` AND `completed = false` AND `reminder_start_date <= today`.
- **Sends** one email per task to the owner's email address through Brevo.
- **Repeats** every day. Tasks stop being selected once completed (or deleted).
- ❓ Email content, failure handling, and how to avoid sending twice on the same day are open.

### 3.4 Environment configuration (names only)

Settings are provided as environment variables: database connection (`DATABASE_URL`), Brevo API key (`BREVO_API_KEY`), session secret (`SESSION_SECRET`) and allowed frontend origin (`FRONTEND_ORIGIN`).
- Locally, the backend reads them from `backend/.env`, which is never committed. `backend/.env.example` lists the names with fake values.
- On Render, they are set in the service's Environment settings.
- The frontend holds no secrets. It only needs the public backend URL, `VITE_BACKEND_URL`, set locally in `frontend/.env` and in the Vercel settings.
- Secrets must never be committed to GitHub.

---

## 4. Testing Approach

- **Backend:** pytest for every endpoint, including the unhappy paths (unverified login, expired code, another user's task).
- **Frontend:** linting on every change. ❓ Linter not chosen.
- **Integration:** every milestone below ends with an integration test where the **deployed or local frontend talks to the real backend**.

---

## 5. Collaboration Rules (from your decisions)

- Git and GitHub, one repository.
- Backend developer: Maurice123-Tech. Frontend developer: Mac Ty.
- Update section 3 of this file before changing any endpoint so both sides stay in sync.
- Do not start the next milestone until the current milestone's integration test passes.
- Branching: the backend developer works on the `backend` branch and the frontend developer on `frontend`. Both merge into `dev` through pull requests, where the milestone is tested together. Only tested work from `dev` is merged into `main`.
- ❓ CI is not decided.

---

## 6. Phased Implementation Roadmap

Each milestone has a **Backend** part, a **Frontend** part and an **Integration test**. A milestone is done only when its integration test passes. The suggested day numbers are a draft pacing for the 1-week deadline. Adjust them as you learn how fast you move.

### Milestone 0: Foundation and first connection (Day 1)

**Backend**
- Create the FastAPI project and connect it to Postgres through SQLAlchemy.
- Add a simple health endpoint that confirms the app and database are reachable.
- Add CORS so the frontend origin can call the backend with credentials.
- Set up pytest and write the first test (health endpoint).
- Deploy to Render.

**Frontend**
- Create the project with Tailwind and a linter.
- Build a basic mobile-first page shell.
- Add a small script that calls the health endpoint and shows the result.
- Deploy to Vercel.

**Integration test:** the page on Vercel shows a success message from the backend on Render, and the same works locally.

### Milestone 1: Sign up and email verification (Day 2)

**Backend**
- `users` table and email-codes table, created with Alembic migrations.
- `POST /auth/signup` with validation and password hashing.
- Send the 6-digit verification code by email through Brevo.
- `POST /auth/verify-email` with the 5-minute expiry, single use, and the 5-wrong-attempts limit.
- `POST /auth/resend-verification` with the 60-second wait.
- pytest: valid signup, duplicate email, invalid input (including a weak password), valid code, wrong code, expired code, reused code, code invalidated after 5 wrong attempts, resend replaces the old code, resend within 60 seconds sends no new code.

**Frontend**
- Sign-up page with field validation and clear error messages.
- A code-entry page shown after sign-up: a 6-digit input, a resend button with a 60-second countdown, and clear messages for a wrong, expired or invalid code.

**Integration test:** sign up from the frontend, receive the real email with the code, enter it within 5 minutes, and see the user marked verified in the database. A code older than 5 minutes is rejected, and after requesting a new code the old one no longer works.

### Milestone 2: Login, session and logout (Day 3)

**Backend**
- `POST /auth/login` that blocks unverified users.
- Session creation, session cookie, `GET /auth/me`, and `POST /auth/logout`.
- A reusable check that makes protected endpoints return `401` without a valid session.
- pytest: correct login, wrong password, unverified user, `me` with and without a session, logout.

**Frontend**
- Login page and logout button.
- Send credentials on every request.
- Redirect to login when `GET /auth/me` returns `401`.
- Clear message for the unverified-user case.

**Integration test:** on the **deployed** Vercel and Render sites, log in, refresh the page and stay logged in, then log out and confirm protected pages are no longer reachable. This is the first real test of the cross-domain cookie (risk R3), so do it early.

### Milestone 3: Password reset (Day 3)

**Backend**
- `POST /auth/forgot-password` and `POST /auth/reset-password`.
- Reset code email through Brevo, with the 10-minute expiry, single use, and the 5-wrong-attempts limit.
- pytest: unknown email, valid reset, wrong code, expired code, reused code, code invalidated after 5 wrong attempts, a new code replaces the old one, weak new password.

**Frontend**
- "Forgot password" page, and a page to enter the code and the new password.
- Success and error messages.

**Integration test:** request a reset, receive the code by email, set a new password, log in with the new password, and confirm the old one no longer works.

### Milestone 4: Create and save a task (Day 4)

**Backend**
- `tasks` table linked to `users`.
- `POST /tasks` with all validation rules from section 2.6, saving to the database.
- pytest: valid task, each invalid field, no session, task belongs to the logged-in user.

**Frontend**
- Mobile-friendly task form: title, description, priority, due date, optional due time, Remind me toggle, reminder start date (shown when the toggle is on).
- Show validation errors per field.
- Confirmation after saving.

**Integration test:** create a task from the frontend and confirm the row exists in the database with the right `user_id`. Invalid inputs show the right error messages. A second user cannot see the first user's task.

### Milestone 5: View, filter and edit tasks (Day 5)

**Backend**
- `GET /tasks` with the `status` filter and `GET /tasks/{task_id}`.
- `PUT /tasks/{task_id}`.
- pytest: each filter value, invalid filter, edit with valid and invalid data, editing someone else's task returns `404`.

**Frontend**
- Task list showing the user's tasks.
- Filter control for All, Completed and Uncompleted.
- Edit form pre-filled from the task.

**Integration test:** the list shows only your own tasks, each filter shows the right set, and an edit made in the UI shows in the list and in the database.

### Milestone 6: Complete and delete tasks (Day 5)

**Backend**
- `PATCH /tasks/{task_id}/complete` and `DELETE /tasks/{task_id}`.
- pytest: complete, delete, both on someone else's task, both on a task that does not exist.

**Frontend**
- A complete control and a delete control on each task, with a confirmation before deleting.
- The list and the filter update right after each action.

**Integration test:** complete a task and see it move to the Completed filter. Delete a task and see it disappear from the list and the database.

### Milestone 7: Automated reminders (Day 6)

> ❓ This milestone cannot start until the team decides what triggers the 6 AM run.

**Backend**
- The reminder job from section 3.3.
- Reminder email through Brevo.
- The scheduling mechanism (once decided) running at 6 AM every day.
- pytest: task selected when `remind_me` is true, not completed and the start date has been reached; not selected when completed, when `remind_me` is false, or when the start date is in the future.

**Frontend**
- Show a clear reminder indicator on tasks with reminders on.
- Make sure marking complete visibly stops reminders (for example by showing the task as completed).

**Integration test:** create a task with Remind me on and a start date of today. Confirm the email arrives at 6 AM. Mark the task complete and confirm no email arrives at the next run.

### Milestone 8: Polish and production readiness (Day 7)

**Backend**
- Review error handling and response messages across all endpoints.
- Confirm secrets are in environment settings and not in the repository.
- Confirm all pytest tests pass.

**Frontend**
- Test every screen at phone width on a real phone and fix layout issues.
- Make errors and empty states friendly (for example, no tasks yet).
- Confirm the linter is clean.

**Integration test:** run the full journey on the live site, on a phone: sign up, verify, log in, create a task with a reminder, edit it, filter, complete it, delete another task, log out, reset the password.

---

## 7. Open Decisions (architecture)

| # | Question |
|---|---|
| A1 | **What triggers the 6 AM reminder run?** This blocks Milestone 7. |
| A2 | Where is session data stored (database table, memory, other)? How long does a session last? |
| A3 | Cookie settings for the cross-domain setup (Vercel to Render), so the browser keeps and sends the cookie |
| A5 | Is "create" and "save" one API call (as drafted) or two separate calls? |
| A8 | How is a duplicate reminder on the same day prevented, and are sent reminders recorded? |
| A9 | Which hashing method is used for passwords and codes? (Both are hashed, the library is chosen when the code is written.) |
| A13 | Endpoint paths in section 3 (all marked ⚠) |

**Decided**
- A4: There are no links. Verification and password reset both use 6-digit codes.
- A6: Primary keys are UUIDs.
- A7: Codes are 6 digits, stored hashed, with a 5-minute expiry for verification and 10 minutes for reset. A new code replaces the old one, with 60 seconds between requests and 5 wrong attempts before a code stops working.
- A10: Alembic is the migration tool.
- A11: Two folders at the repository root: `backend/` and `frontend/`.
- A12: Environment variables, with `.env` locally and each host's settings in production (see 3.4).
