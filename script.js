
async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
    }

    return data;
}


// STUDENT DASHBOARD
const complaintForm = document.getElementById("complaintForm");

if (complaintForm) {

    complaintForm.addEventListener("submit", async function(event) {
        event.preventDefault();

        const category = document.getElementById("category").value;
        const priority = document.getElementById("priority").value;
        const description = document.getElementById("description").value;

        try {
            const result = await apiRequest("/api/complaints", {
                method: "POST",
                body: JSON.stringify({
                    category,
                    priority,
                    description
                })
            });

            document.getElementById("studentMessage").textContent =
                result.message;

            complaintForm.reset();
            loadStudentComplaints();

        } catch (error) {
            document.getElementById("studentMessage").textContent =
                error.message;
        }
    });

    loadStudentComplaints();
}


async function loadStudentComplaints() {
    const tbody = document.getElementById("studentComplaints");

    try {
        const complaints = await apiRequest("/api/complaints");
        console.log("LOAD FUNCTION DATA:", complaints);
        tbody.innerHTML = "";

        if (complaints.length === 0) {
            tbody.innerHTML =
                '<tr><td colspan="8">No complaints submitted yet.</td></tr>';
            return;
        }

        complaints.forEach(item => {
            const row = document.createElement("tr");

            const values = [
                item.complaint_id,
                item.category,
                item.priority,
                item.status,
                item.assigned_to || "Not assigned",
                item.resolution || "Not available",
                item.created_at || ""
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            const historyCell = document.createElement("td");
            const historyButton = document.createElement("button");
            historyButton.textContent = "View History";
            historyButton.addEventListener("click", () => {
                showHistory(item.complaint_id, "studentHistory");
            });

            historyCell.appendChild(historyButton);
            row.appendChild(historyCell);
            tbody.appendChild(row);
        });

    } catch (error) {
        tbody.innerHTML =
            `<tr><td colspan="8">${error.message}</td></tr>`;
    }
}


// FACULTY DASHBOARD
const facultyTable = document.getElementById("facultyComplaints");

if (facultyTable) {
    loadFacultyComplaints();

    document.getElementById("searchComplaint")
        .addEventListener("input", loadFacultyComplaints);
}


async function loadFacultyComplaints() {
    const tbody = document.getElementById("facultyComplaints");

    try {
        const complaints = await apiRequest("/api/complaints");

        document.getElementById("totalCount").textContent =
            complaints.length;

        document.getElementById("pendingCount").textContent =
            complaints.filter(c =>
                !["Resolved", "Rejected"].includes(c.status)
            ).length;

        document.getElementById("resolvedCount").textContent =
            complaints.filter(c => c.status === "Resolved").length;

        const search = document.getElementById("searchComplaint")
            .value.toLowerCase();

        const filtered = complaints.filter(c =>
            String(c.complaint_id).includes(search) ||
            (c.student_name || "").toLowerCase().includes(search)
        );

        tbody.innerHTML = "";

        if (filtered.length === 0) {
            tbody.innerHTML =
                '<tr><td colspan="9">No complaints found.</td></tr>';
            return;
        }

        filtered.forEach(item => {
            const row = document.createElement("tr");

            function addCell(value) {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            }

            addCell(item.complaint_id);
            addCell(item.student_name);
            addCell(item.category);
            addCell(item.description);
            addCell(item.priority);

            // Staff assignment
            const staffCell = document.createElement("td");
            const staffInput = document.createElement("input");
            staffInput.value = item.assigned_to || "";
            staffInput.placeholder = "Staff name";
            staffCell.appendChild(staffInput);
            row.appendChild(staffCell);

            // Status
            const statusCell = document.createElement("td");
            const statusSelect = document.createElement("select");

            ["Submitted", "Assigned", "In Progress",
             "Resolved", "Rejected"].forEach(status => {
                const option = document.createElement("option");
                option.value = status;
                option.textContent = status;
                if (status === item.status) option.selected = true;
                statusSelect.appendChild(option);
            });

            statusCell.appendChild(statusSelect);
            row.appendChild(statusCell);

            // Resolution
            const resolutionCell = document.createElement("td");
            const resolutionInput = document.createElement("textarea");
            resolutionInput.value = item.resolution || "";
            resolutionInput.placeholder = "Enter resolution";
            resolutionCell.appendChild(resolutionInput);
            row.appendChild(resolutionCell);

            // Save and history buttons
            const actionCell = document.createElement("td");

            const saveButton = document.createElement("button");
            saveButton.textContent = "Save";

            saveButton.addEventListener("click", async () => {
                try {
                    const result = await apiRequest(
                        `/api/complaints/${item.complaint_id}/update`,
                        {
                            method: "POST",
                            body: JSON.stringify({
                                assigned_to: staffInput.value,
                                status: statusSelect.value,
                                resolution: resolutionInput.value
                            })
                        }
                    );

                    alert(result.message);
                    loadFacultyComplaints();

                } catch (error) {
                    alert(error.message);
                }
            });

            const historyButton = document.createElement("button");
            historyButton.textContent = "History";

            historyButton.addEventListener("click", () => {
                showHistory(item.complaint_id, "facultyHistory");
            });

            actionCell.appendChild(saveButton);
            actionCell.appendChild(historyButton);
            row.appendChild(actionCell);

            tbody.appendChild(row);
        });

    } catch (error) {
        tbody.innerHTML =
            `<tr><td colspan="9">${error.message}</td></tr>`;
    }
}


// SHOW COMPLAINT HISTORY
async function showHistory(complaintId, containerId) {
    const container = document.getElementById(containerId);

    try {
        const history = await apiRequest(
            `/api/complaints/${complaintId}/history`
        );

        container.innerHTML = `<h3>History - Complaint #${complaintId}</h3>`;

        if (history.length === 0) {
            container.textContent = "No history available.";
            return;
        }

        history.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";

            const details = document.createElement("p");
            details.textContent =
                `${item.old_status || "New"} → ${item.new_status}`;

            const remarks = document.createElement("p");
            remarks.textContent = item.remarks || "";

            const date = document.createElement("small");
            date.textContent = item.changed_at || "";

            div.appendChild(details);
            div.appendChild(remarks);
            div.appendChild(date);

            container.appendChild(div);
        });

        container.scrollIntoView({ behavior: "smooth" });

    } catch (error) {
        container.textContent = error.message;
    }
}
