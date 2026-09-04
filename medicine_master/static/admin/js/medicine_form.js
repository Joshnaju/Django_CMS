// @ts-nocheck
document.addEventListener("DOMContentLoaded", function () {
  const dosageForm = document.getElementById("id_dosage_form");

  const strengthField = document
    .getElementById("id_strength")
    .closest(".form-row");

  const strengthUnitField = document
    .getElementById("id_strength_unit")
    .closest(".form-row");

  function toggleStrengthFields() {
    if (dosageForm.value === "POWDER") {
      strengthField.style.display = "none";
      strengthUnitField.style.display = "none";

      // Clear values
      document.getElementById("id_strength").value = "";
      document.getElementById("id_strength_unit").value = "";
    } else {
      strengthField.style.display = "";
      strengthUnitField.style.display = "";
    }
  }

  dosageForm.addEventListener("change", toggleStrengthFields);

  // Run when page loads
  toggleStrengthFields();
});
