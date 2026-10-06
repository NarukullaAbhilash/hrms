const API_URL = "http://127.0.0.1:8000";

const loginForm = document.getElementById("loginForm");
const loginButton = document.getElementById("loginButton");
const message = document.getElementById("message");


/* ============================================================
   LOGIN
============================================================ */

loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email =
        document.getElementById("email").value.trim();

    const password =
        document.getElementById("password").value;

    message.textContent = "";

    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";


    try {

        const response = await fetch(
            `${API_URL}/auth/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );


        const data = await response.json();


        /* ====================================================
           LOGIN ERROR
        ==================================================== */

        if (!response.ok) {

            message.textContent =
                data.detail || "Login failed.";

            loginButton.disabled = false;
            loginButton.textContent = "Login";

            return;
        }


        /* ====================================================
           VALIDATE LOGIN RESPONSE
        ==================================================== */

        if (!data.access_token || !data.user) {

            message.textContent =
                "Invalid login response from server.";

            loginButton.disabled = false;
            loginButton.textContent = "Login";

            return;
        }


        /* ====================================================
           SAVE JWT TOKEN
        ==================================================== */

        localStorage.setItem(
            "access_token",
            data.access_token
        );


        /* ====================================================
           SAVE USER INFORMATION
        ==================================================== */

        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );


        message.textContent =
            "Login successful!";


        /* ====================================================
           ROLE-BASED NAVIGATION
        ==================================================== */

        const role = data.user.role;


        /* ----------------------------------------------------
           ADMIN
        ---------------------------------------------------- */

        if (role === "admin") {

            window.location.href = "admin.html";

            return;
        }


        /* ----------------------------------------------------
           HR
        ---------------------------------------------------- */

        if (role === "hr") {

            window.location.href = "admin.html";

            return;
        }


        /* ----------------------------------------------------
           EMPLOYEE
        ---------------------------------------------------- */

        if (role === "employee") {

            window.location.href = "employee.html";

            return;
        }


        /* ----------------------------------------------------
           UNKNOWN ROLE
        ---------------------------------------------------- */

        message.textContent =
            "Unknown user role.";

        localStorage.removeItem("access_token");
        localStorage.removeItem("user");

        loginButton.disabled = false;
        loginButton.textContent = "Login";


    } catch (error) {

        console.error(
            "Login error:",
            error
        );

        message.textContent =
            "Unable to connect to HRMS server.";

        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }

});