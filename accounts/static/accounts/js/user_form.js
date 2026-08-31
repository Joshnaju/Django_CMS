// @ts-nocheck
document.addEventListener("DOMContentLoaded", function () {
  const roleField = document.getElementById("id_role");
  const departmentRow = document
    .getElementById("id_department")
    .closest(".form-row");
  const feeRow = document
    .getElementById("id_consultation_fee")
    .closest(".form-row");

  function toggleDoctorFields() {
    if (roleField.value === "DOCTOR") {
      departmentRow.style.display = "";
      feeRow.style.display = "";
    } else {
      departmentRow.style.display = "none";
      feeRow.style.display = "none";
    }
  }

  roleField.addEventListener("change", toggleDoctorFields);

  toggleDoctorFields();
});
