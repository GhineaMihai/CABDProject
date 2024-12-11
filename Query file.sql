SELECT table_name 
FROM user_tables;

//1. 

CREATE TABLE Projects (
    project_id NUMBER PRIMARY KEY,
    project_name VARCHAR2(200),
    client VARCHAR2(200),
    budget NUMBER,
    valid_start_time DATE NOT NULL, --data de la care e valid proiectul
    valid_end_time DATE,  --data la care s-a incheiat proiectul
    CONSTRAINT chk_projects_valid_time CHECK (valid_end_time IS NULL OR valid_start_time < valid_end_time)
);


CREATE TABLE Projects_History (
    project_id NUMBER,
    project_name VARCHAR2(200),
    client VARCHAR2(200),
    budget NUMBER,
    valid_start_time DATE NOT NULL,
    valid_end_time DATE,
    Action VARCHAR(10),
    Transaction_Start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Start of this transaction
    Transaction_End TIMESTAMP,  -- End of this transaction (null for active)
    PRIMARY KEY (project_id, Transaction_Start)
);


CREATE TABLE Employees (
    employee_id NUMBER PRIMARY KEY,
    name VARCHAR2(100),
    position VARCHAR2(100)
);

CREATE TABLE Employees_History (
    employee_id NUMBER,
    name VARCHAR2(100),
    position VARCHAR2(100),
    Action VARCHAR(10),
    Transaction_Start TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Start of this transaction (when employee was hired)
    Transaction_End TIMESTAMP,  -- End of this transaction (when employee changed position)
    PRIMARY KEY (employee_id, Transaction_Start)
);


CREATE TABLE Assignments (
    assignment_id NUMBER PRIMARY KEY,
    employee_id NUMBER REFERENCES Employees(employee_id) ON DELETE CASCADE,
    project_id NUMBER REFERENCES Projects(project_id) ON DELETE CASCADE,
    points NUMBER,
    start_time DATE NOT NULL, -- start date of the assignment
    end_time DATE  -- end date of the assignment
);

CREATE TABLE Assignments_History (
    assignment_id NUMBER,
    employee_id NUMBER REFERENCES Employees(employee_id) ON DELETE CASCADE,
    project_id NUMBER REFERENCES Projects(project_id) ON DELETE CASCADE,
    points NUMBER,
    start_time DATE NOT NULL,
    end_time DATE,
    Action VARCHAR(10),
    Transaction_Start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Start of this transaction (when an assignment started) 
    Transaction_End   TIMESTAMP, -- the end of this assignment transaction  
    PRIMARY KEY (assignment_id, Transaction_Start)
);


DROP TABLE Assignments;
DROP TABLE Assignments_History;
DROP TABLE Projects;
DROP TABLE Projects_History;
DROP TABLE Employees;
DROP TABLE Employees_History


CREATE OR REPLACE TRIGGER trg_employee_history
AFTER INSERT OR UPDATE OR DELETE ON Employees
FOR EACH ROW
DECLARE
    v_transaction_time_start TIMESTAMP;
    operation_type VARCHAR2(10);
BEGIN
    -- Determine the action type
    IF INSERTING THEN
        operation_type := 'INSERT';
    ELSIF UPDATING THEN
        operation_type := 'UPDATE';
    ELSIF DELETING THEN
        operation_type := 'DELETE';
    END IF;

    -- Set transaction time start to the current timestamp
    v_transaction_time_start := SYSTIMESTAMP;

    IF INSERTING THEN
        -- For insert, set transaction_start to current time and transaction_end to NULL
        INSERT INTO employees_history
        (employee_id, name, position, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.employee_id, :NEW.name, :NEW.position, operation_type, v_transaction_time_start, NULL);

    ELSIF UPDATING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE employees_history
        SET Transaction_End = v_transaction_time_start
        WHERE employee_id = :OLD.employee_id
        AND Transaction_End IS NULL;

        -- Insert a new record into employee_history to log the update
        INSERT INTO employees_history
        (employee_id, name, position, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.employee_id, :NEW.name, :NEW.position, operation_type, v_transaction_time_start, NULL);

    ELSIF DELETING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE employees_history
        SET Transaction_End = v_transaction_time_start
        WHERE employee_id = :OLD.employee_id
        AND Transaction_End IS NULL;

        -- Insert a new record into employees_history to log the delete action
        INSERT INTO employees_history
        (employee_id, name, position, Action, Transaction_Start, Transaction_End)
        VALUES
        (:OLD.employee_id, :OLD.name, :OLD.position, operation_type, v_transaction_time_start, NULL);
    END IF;
END;


CREATE OR REPLACE TRIGGER trg_projects_history
AFTER INSERT OR UPDATE OR DELETE ON Projects
FOR EACH ROW
DECLARE
    v_transaction_time_start TIMESTAMP;
    operation_type VARCHAR2(10);
BEGIN
    -- Determine the action type
    IF INSERTING THEN
        operation_type := 'INSERT';
    ELSIF UPDATING THEN
        operation_type := 'UPDATE';
    ELSIF DELETING THEN
        operation_type := 'DELETE';
    END IF;

    -- Set transaction time start to the current timestamp
    v_transaction_time_start := SYSTIMESTAMP;

    IF INSERTING THEN
        -- For insert, set transaction_start to current time and transaction_end to NULL
        INSERT INTO Projects_History
        (project_id, project_name, client, budget, valid_start_time, valid_end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.project_id, :NEW.project_name, :NEW.client, :NEW.budget, :NEW.valid_start_time, :NEW.valid_end_time, operation_type, v_transaction_time_start, NULL);

    ELSIF UPDATING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE Projects_History
        SET Transaction_End = v_transaction_time_start
        WHERE project_id = :OLD.project_id
        AND Transaction_End IS NULL;

        -- Insert a new record into Projects_History to log the update
        INSERT INTO Projects_History
        (project_id, project_name, client, budget, valid_start_time, valid_end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.project_id, :NEW.project_name, :NEW.client, :NEW.budget, :NEW.valid_start_time, :NEW.valid_end_time, operation_type, v_transaction_time_start, NULL);


    ELSIF DELETING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE Projects_History
        SET Transaction_End = v_transaction_time_start
        WHERE project_id = :OLD.project_id
        AND Transaction_End IS NULL;

        -- Insert a new record into Projects_History to log the delete action
        INSERT INTO Projects_History
        (project_id, project_name, client, budget, valid_start_time, valid_end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:OLD.project_id, :OLD.project_name, :OLD.client, :OLD.budget, :OLD.valid_start_time, :OLD.valid_end_time, operation_type, v_transaction_time_start, NULL);
    END IF;
END;


CREATE OR REPLACE TRIGGER trg_assignments_history
AFTER INSERT OR UPDATE OR DELETE ON Assignments
FOR EACH ROW
DECLARE
    v_transaction_time_start TIMESTAMP;
    operation_type VARCHAR2(10);
BEGIN
    -- Determine the action type
    IF INSERTING THEN
        operation_type := 'INSERT';
    ELSIF UPDATING THEN
        operation_type := 'UPDATE';
    ELSIF DELETING THEN
        operation_type := 'DELETE';
    END IF;

    -- Set transaction time start to the current timestamp
    v_transaction_time_start := SYSTIMESTAMP;

    IF INSERTING THEN
        -- For insert, set transaction_start to current time and transaction_end to NULL
        INSERT INTO Assignments_History
        (assignment_id, employee_id, project_id, points, start_time, end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.assignment_id, :NEW.employee_id, :NEW.project_id, :NEW.points, :NEW.start_time, :NEW.end_time, operation_type, v_transaction_time_start, NULL);

    ELSIF UPDATING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE Assignments_History
        SET Transaction_End = v_transaction_time_start
        WHERE assignment_id = :OLD.assignment_id
        AND Transaction_End IS NULL;

        -- Insert a new record into Assignments_History to log the update
        INSERT INTO Assignments_History
        (assignment_id, employee_id, project_id, points, start_time, end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:NEW.assignment_id, :NEW.employee_id, :NEW.project_id, :NEW.points, :NEW.start_time, :NEW.end_time, operation_type, v_transaction_time_start, NULL);


    ELSIF DELETING THEN
        -- Update transaction_end for the most recent history record with Transaction_End as NULL
        UPDATE Assignments_History
        SET Transaction_End = v_transaction_time_start
        WHERE assignment_id = :OLD.assignment_id
        AND Transaction_End IS NULL;

        -- Insert a new record into Assignments_History to log the delete action
        INSERT INTO Assignments_History
        (assignment_id, employee_id, project_id, points, start_time, end_time, Action, Transaction_Start, Transaction_End)
        VALUES
        (:OLD.assignment_id, :OLD.employee_id, :OLD.project_id, :OLD.points, :OLD.start_time, :OLD.end_time, operation_type, v_transaction_time_start, NULL);
    END IF;
END;


//2.

/*Creati scripturi de populare cu date (INSERT) a cel putin 100 de inregistrari
pentru entitatile de mai sus, datele calendaristice sa nu fie mai vechi
de 15 septembrie 2024*/

//Popularea tabelei Employees
BEGIN
   FOR i IN 1..100 LOOP
      INSERT INTO Employees (employee_id, name, position)
      VALUES (
         i,
         'Employee_' || i, 
         CASE 
            WHEN MOD(i, 4) = 0 THEN 'Manager'
            WHEN MOD(i, 4) = 1 THEN 'Developer'
            WHEN MOD(i, 4) = 2 THEN 'Tester'
            ELSE 'Data Analyst'
         END
      );
   END LOOP;
END;

Select * FROM Employees;


//Popularea tabelei Projects

BEGIN
   FOR i IN 1..100 LOOP
      INSERT INTO Projects (project_id, project_name, client, budget, valid_start_time, valid_end_time)
      VALUES (
         i,
         'Project_' || i, 
         'Client_' || i, 
         round(DBMS_RANDOM.VALUE(100, 5000)), 
         TO_DATE('2024-09-15', 'YYYY-MM-DD') + DBMS_RANDOM.VALUE(1, 60), 
         TO_DATE('2025-01-15', 'YYYY-MM-DD') - DBMS_RANDOM.VALUE(1, 30)
      );
   END LOOP;
END;

SELECT * FROM Projects;




//Popularea Tabelei Assignments

BEGIN
   FOR i IN 1..100 LOOP
      INSERT INTO Assignments (assignment_id, employee_id, project_id, points, start_time, end_time)
      VALUES (
         i,
         i,  
         i,  
         i+i, 
         TO_DATE('2024-09-15', 'YYYY-MM-DD') + DBMS_RANDOM.VALUE(60, 70), 
         TO_DATE('2024-12-31', 'YYYY-MM-DD') - DBMS_RANDOM.VALUE(1, 15)
      );
   END LOOP;
END;


SELECT * FROM Assignments;

commit;

/*Creati scripturi de modificare a datelor (UPDATE) de minim 5, maxim 10 ori
pentru cel putin 5 inregistrari din tabelele de baza de mai sus*/


//Update Position 5 intrari pe tablea de Employees
BEGIN
    For j in 1..5 LOOP
        FOR i IN 1..5 LOOP
            UPDATE Employees
            SET position = 'Updated Position ' || j
            WHERE employee_id = i;
        END LOOP;
    END LOOP;
END;

SELECT * FROM Employees;

//Update budget la 5 intrari pe tabela de Projects
BEGIN
    For j in 1..5 LOOP
        FOR i IN 1..5 LOOP
            UPDATE Projects
            SET budget = round(DBMS_RANDOM.VALUE(100, 5000))
            WHERE project_id = i;
        END LOOP;
    END LOOP;
END;

SELECT * FROM Projects;

//Update valid_start_time si valid_end_time la 5 intrari pe tabela de Assignments
BEGIN
    FOR j in 1..5 LOOP
        FOR i IN 1..5 LOOP
            UPDATE Assignments
            SET points = i+j,
                start_time = start_time + INTERVAL '1' DAY,
                end_time = end_time - INTERVAL '1' DAY
            WHERE assignment_id = i;
        END LOOP;
    END LOOP;
END;

SELECT * FROM Assignments;

commit;
/*Creati scripturi de stergere (DELETE) a cel putin 3 inregistrari
din tabelele de baza de mai sus*/

DELETE FROM Assignments
WHERE assignment_id IN (5, 6, 7, 8);

SELECT * FROM Assignments;

DELETE FROM Employees
WHERE employee_id IN (6, 7, 8);

SELECT * FROM Employees;

DELETE FROM Projects
WHERE project_id IN (5, 6, 7, 8);

SELECT * FROM Projects;

commit;

//3

/*din entitatea cu atribute valid time, sa se returneze intervalul in care randul 
(inregistrarea) actualizat cel mai recent a avut valoarea maxima pentru un camp numeric
ales la implementare*/

--cel mai recent modificat proiect si care a fost bugetul maxim
WITH last_updated AS(
SELECT * FROM Projects_History
Order by Transaction_Start desc
FETCH FIRST 1 ROW ONLY)

Select h.project_id, h.budget, h.client, h.transaction_start, h.transaction_end 
from Projects_History h join last_updated LU on h.project_id=lu.project_id
Order by h.budget desc
FETCH FIRST ROW ONLY


/*dintr-o entitate cu atribute transaction time, sa se returneze numarul de randuri
ce au avut operatii asupra lor (INSERT/DELETE/UPDATE) din fiecare saptamana, 
din ultimele 4 saptamani*/

SELECT     
    TO_CHAR(TRUNC(transaction_start, 'IW'), 'DD Mon YYYY') || ' - ' || TO_CHAR(TRUNC(transaction_start, 'IW') + INTERVAL '6' DAY, 'DD Mon YYYY') AS week,
     action, COUNT(*) AS num_operations
FROM Projects_History
WHERE transaction_start >= TRUNC(SYSDATE, 'IW') - INTERVAL '21' DAY
GROUP BY TRUNC(transaction_start, 'IW'), action
ORDER BY week, action;


/*cel putin 3 operatii (diferite) pentru date temporale care sa aiba rezultat numeric*/

//cati Employees au avut datele modificate pana acum

SELECT COUNT(DISTINCT employee_id) AS nr_modified_employees
FROM Employees_History
WHERE Transaction_End IS not NULL;


//cel mai mare buget din ultima saptamana (de pe un proiect)
SELECT project_id, budget
FROM Projects_History
WHERE Transaction_Start >= TRUNC(SYSDATE, 'IW')
ORDER BY budget DESC
FETCH FIRST 1 ROW ONLY;

//de cate ori a fost modificata un Employee in ultima saptamana
Select employee_id, Count(*) as modified_last_week
from Employees_History
where employee_id = 1 and transaction_start >= TRUNC(SYSDATE, 'IW') 
group by employee_id


//cel putin 3 operatii (diferite) pentru date temporale care sa aiba rezultat temporal

// data la care s-a facut cel mai recent assignment
SELECT MAX(start_time) AS Most_Recent
FROM Assignments

//cand a fost modificat ultima data un employee
SELECT MAX(transaction_start) AS last_updated
FROM Employees_History
WHERE employee_id = 1;

//data la care a fost sters un Assignment
DELETE FROM Assignments
WHERE assignment_id = 46;

Select TranSaction_Start
From Assignments_History
Where assignment_id = 46 and action='DELETE'


//cel putin 2 operatii (diferite) pentru date temporale care sa aiba rezultat boolean

//verifcam daca un proiect se incheie pana luna urmatoare
SELECT 
    project_id, 
    valid_end_time, 
    CASE 
        WHEN valid_end_time IS NOT NULL AND valid_end_time <= ADD_MONTHS(SYSDATE, 1) THEN 'TRUE' 
        ELSE 'FALSE' 
    END AS Return_This_Month
FROM Projects
WHERE project_id=44

//verificam daca un Proiect are data de incheiere
SELECT 
    project_id, 
    valid_end_time, 
    CASE 
        WHEN valid_end_time IS NOT NULL THEN 'TRUE' 
        ELSE 'FALSE' 
    END AS HAS_END_DATE
FROM Projects
WHERE project_id=44
