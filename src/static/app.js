document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  // Helper to escape HTML (prevent XSS)
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Build the HTML for an activity card
  function buildCardHtml(name, details) {
    const spotsLeft = details.max_participants - details.participants.length;

    const participantsHtml =
      details.participants && details.participants.length
        ? `<p><strong>Participants:</strong></p>
          <ul class="participants-list">
            ${details.participants
              .map((p) => {
                const local = p.split("@")[0] || "";
                const initials = local
                  .split(/[\.\-_]/)
                  .map((s) => s.charAt(0))
                  .join("")
                  .slice(0, 2)
                  .toUpperCase();
                return `<li>
                  <span class="participant-chip" title="${escapeHtml(p)}">
                    <span class="avatar">${escapeHtml(initials)}</span>
                    <span class="email-text">${escapeHtml(p)}</span>
                  </span>
                </li>`;
              })
              .join("")}
          </ul>`
        : `<p><strong>Participants:</strong> None</p>`;

    return `
      <h4>${escapeHtml(name)}</h4>
      <p>${escapeHtml(details.description)}</p>
      <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
      <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
      ${participantsHtml}
    `;
  }

  // Helper to find a card element for an activity by name
  function findCardByName(name) {
    return Array.from(activitiesList.children).find((c) => c.dataset.activity === name);
  }

  // Update or create a single activity card
  function upsertActivityCard(name, details) {
    let card = findCardByName(name);
    if (!card) {
      card = document.createElement("div");
      card.className = "activity-card";
      card.dataset.activity = name;
      activitiesList.appendChild(card);

      // Also ensure the select contains this activity
      const exists = Array.from(activitySelect.options).some((o) => o.value === name);
      if (!exists) {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      }
    }
    card.innerHTML = buildCardHtml(name, details);
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Render all activities (initial load)
      Object.entries(activities).forEach(([name, details]) => {
        upsertActivityCard(name, details);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Update only the activity card that was signed up to
        try {
          const aResp = await fetch(`/activities/${encodeURIComponent(activity)}`);
          if (aResp.ok) {
            const details = await aResp.json();
            upsertActivityCard(activity, details);
          } else {
            // Fallback: refresh all activities
            await fetchActivities();
          }
        } catch (e) {
          console.error("Failed to refresh single activity:", e);
          await fetchActivities();
        }
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
