\# HRMS - Human Resource Management System



A complete Human Resource Management System built using FastAPI, SQLAlchemy, SQLite, JWT Authentication, Role-Based Access Control, and a frontend dashboard.



\## Project Overview



The HRMS manages employees, attendance, leave, payroll, salary slips, reports, notifications, audit logs, and role-based access.



\## Technologies Used



\### Backend

\- Python

\- FastAPI

\- SQLAlchemy

\- SQLite

\- JWT Authentication

\- Pydantic

\- ReportLab



\### Frontend

\- HTML

\- CSS

\- JavaScript



\### API Testing

\- Swagger UI

\- Postman



\### Database

\- SQLite

\- SQLAlchemy ORM



\## User Roles



The system supports three roles:



\### Admin

\- Manage users

\- Manage employees

\- Activate/deactivate employees

\- Manage attendance

\- Manage leave

\- Generate payroll

\- Lock payroll

\- Credit salary

\- Download salary slips

\- View reports

\- View audit logs



\### HR

\- Manage employee information

\- Manage attendance

\- Manage leave

\- Generate payroll

\- Manage salary processing

\- View reports



\### Employee

\- View own profile

\- Check in

\- Check out

\- View attendance

\- Apply for leave

\- View leave balance

\- View salary slips



\## Main Features



\### Authentication

\- User registration

\- User login

\- JWT access tokens

\- Password hashing

\- Protected API endpoints

\- Active/inactive user validation



\### Role-Based Access Control

\- Admin authorization

\- HR authorization

\- Employee authorization

\- Admin/HR protected endpoints



\### Employee Management

\- Create employee

\- View employees

\- View employee details

\- Update employee

\- Activate employee

\- Deactivate employee

\- Employee document upload

\- Employee profile endpoint



\### Attendance Management

\- Employee check-in

\- Employee check-out

\- Duplicate check-in prevention

\- Duplicate check-out prevention

\- Working hours calculation

\- Attendance history

\- Monthly attendance summary



\### Leave Management

\- Apply for leave

\- View own leaves

\- View leave balance

\- Approve leave

\- Reject leave

\- Leave balance deduction

\- Loss of Pay tracking

\- Leave overlap validation

\- Email notifications



\### Payroll Management

\- Monthly payroll generation

\- Working-day calculation

\- Present-day calculation

\- Approved leave calculation

\- LOP calculation

\- LOP salary deduction

\- Gross salary calculation

\- Net salary calculation

\- Payroll locking

\- Salary credit simulation

\- Payroll email notification



\### Salary Slips

\- Generate salary slip PDF

\- Download salary slip

\- Employee salary slip access

\- Admin/HR salary slip access



\### Reports

\- Employee CSV report

\- Employee PDF report

\- Attendance CSV report

\- Attendance PDF report

\- Leave CSV report

\- Leave PDF report

\- Payroll CSV report

\- Payroll PDF report



\### Audit Logs

The system records important activities such as:



\- Employee creation

\- Employee update

\- Employee activation/deactivation

\- Document upload

\- Attendance check-in

\- Attendance check-out

\- Leave application

\- Leave approval/rejection

\- Payroll generation

\- Payroll locking

\- Salary credit

\- Salary slip download

\- User role changes



\## Project Structure



```text

hrms/

│

├── backend/

│   ├── app/

│   │   ├── auth/

│   │   ├── models/

│   │   ├── routers/

│   │   ├── schemas/

│   │   ├── services/

│   │   ├── database.py

│   │   └── main.py

│   │

│   ├── hrms.db

│   └── requirements.txt

│

├── database/

│   └── hrms\_schema.sql

│

├── frontend/

│

├── postman/

│   ├── hrms\_openapi.json

│   └── HRMS\_API.postman\_collection.json

│

├── .gitignore

└── README.md

