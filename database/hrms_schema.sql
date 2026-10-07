-- HRMS Database Schema --
-- SQLite

CREATE TABLE attendance (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	attendance_date DATE NOT NULL, 
	check_in DATETIME, 
	check_out DATETIME, 
	working_hours FLOAT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);

CREATE TABLE audit_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	user_email VARCHAR(255), 
	action VARCHAR(100) NOT NULL, 
	entity VARCHAR(100), 
	entity_id INTEGER, 
	description TEXT NOT NULL, 
	timestamp DATETIME NOT NULL, 
	ip_address VARCHAR(100), 
	PRIMARY KEY (id)
);

CREATE TABLE employees (
	id INTEGER NOT NULL, 
	employee_code VARCHAR(50) NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	department VARCHAR(100) NOT NULL, 
	designation VARCHAR(100) NOT NULL, 
	joining_date DATE NOT NULL, 
	salary FLOAT NOT NULL, 
	document VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE leave_balances (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	casual_leave FLOAT NOT NULL, 
	sick_leave FLOAT NOT NULL, 
	earned_leave FLOAT NOT NULL, 
	lop_days FLOAT NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);

CREATE TABLE leaves (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	leave_type VARCHAR(50) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	total_days FLOAT NOT NULL, 
	reason VARCHAR(500), 
	status VARCHAR(20) NOT NULL, 
	approved_by INTEGER, 
	applied_at DATETIME NOT NULL, 
	approved_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
);

CREATE TABLE payroll (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	month INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	basic_salary FLOAT NOT NULL, 
	working_days INTEGER NOT NULL, 
	present_days INTEGER NOT NULL, 
	approved_leave_days FLOAT NOT NULL, 
	lop_days FLOAT NOT NULL, 
	lop_deduction FLOAT NOT NULL, 
	gross_salary FLOAT NOT NULL, 
	net_salary FLOAT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	generated_at DATETIME NOT NULL, 
	locked_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id)
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

