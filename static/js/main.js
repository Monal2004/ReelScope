/* ReelScope — shared interface behaviour (no frameworks). */
(() => {
  "use strict";

  /* ------------------------------------------------------------- Header */

  const header = document.querySelector("[data-header]");
  if (header) {
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------------------------------------------------------- Mobile nav */

  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-nav]");
  if (navToggle && nav) {
    const setNav = (open) => {
      nav.classList.toggle("is-open", open);
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };

    navToggle.addEventListener("click", () => setNav(!nav.classList.contains("is-open")));
    nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setNav(false)));

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setNav(false);
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 760) setNav(false);
    });
  }

  /* --------------------------------------------------------- Staff nav */

  const staffSidebar = document.querySelector("[data-staff-sidebar]");
  const staffToggle = document.querySelector("[data-staff-toggle]");
  const staffScrim = document.querySelector("[data-staff-scrim]");
  if (staffSidebar && staffToggle && staffScrim) {
    const setStaffNav = (open) => {
      staffSidebar.classList.toggle("is-open", open);
      staffScrim.hidden = !open;
      staffToggle.setAttribute("aria-expanded", String(open));
      document.body.style.overflow = open ? "hidden" : "";
    };

    staffToggle.addEventListener("click", () => setStaffNav(!staffSidebar.classList.contains("is-open")));
    staffScrim.addEventListener("click", () => setStaffNav(false));
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setStaffNav(false);
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth > 860) setStaffNav(false);
    });
  }

  /* -------------------------------------------------------------- Toasts */

  document.querySelectorAll("[data-toast]").forEach((toast) => {
    const close = () => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-6px)";
      window.setTimeout(() => toast.remove(), 250);
    };

    toast.querySelector("[data-toast-close]")?.addEventListener("click", close);
    window.setTimeout(close, 6000);
  });

  /* ------------------------------------------------------- Character count */

  document.querySelectorAll("[data-char-count]").forEach((output) => {
    const field = document.getElementById(output.dataset.for);
    if (!field) return;
    const limit = field.getAttribute("maxlength");
    const update = () => {
      output.textContent = field.value.length;
      if (limit && Number(output.textContent) >= Number(limit)) {
        output.style.color = "var(--negative)";
      } else {
        output.style.color = "";
      }
    };
    field.addEventListener("input", update);
    update();
  });

  /* ---------------------------------------------------------- Star rating */

  document.querySelectorAll("[data-star-rating]").forEach((group) => {
    const inputs = Array.from(group.querySelectorAll('input[type="radio"]'));
    const labels = Array.from(group.querySelectorAll(".star-choice"));
    const readout = group.querySelector("[data-star-readout]");
    if (!inputs.length) return;

    const render = (value) => {
      labels.forEach((label, index) => label.classList.toggle("is-active", index < value));
      if (readout) {
        if (value > 0) {
          readout.textContent = `${value} of 5`;
          readout.classList.add("is-set");
        } else {
          readout.textContent = "Choose a rating";
          readout.classList.remove("is-set");
        }
      }
    };

    inputs.forEach((input) => {
      input.addEventListener("change", () => render(Number(input.value)));
    });

    render(Number(inputs.find((input) => input.checked)?.value || 0));
  });

  /* ---------------------------------------------------------- Copy button */

  document.querySelectorAll("[data-copy-button]").forEach((button) => {
    button.addEventListener("click", async () => {
      const value = button.closest(".tracking-value-row")?.querySelector("[data-copy-value]")?.textContent.trim();
      if (!value) return;
      const original = button.textContent;

      try {
        await navigator.clipboard.writeText(value);
        button.textContent = "Copied";
      } catch (_) {
        window.prompt("Copy your Tracking ID:", value);
      }

      window.setTimeout(() => { button.textContent = original; }, 2000);
    });
  });

  /* ------------------------------------------------------ Uppercase ID field */

  document.querySelectorAll('input[name="tracking_id"]').forEach((input) => {
    input.addEventListener("input", () => {
      const position = input.selectionStart;
      input.value = input.value.toUpperCase();
      if (position !== null) input.setSelectionRange(position, position);
    });
  });
})();
