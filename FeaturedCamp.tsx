const API_BASE = "https://findcamp-production.up.railway.app";

const registrationUrl =
  "https://docs.google.com/forms/d/e/1FAIpQLScSMYBOK7SM5C_4gNh1SyXmo7w5WjeZRyCKdnQ6LGpCr13Dyg/viewform?usp=header&utm_source=findcamp&utm_medium=referral&utm_campaign=featured";

export default function FeaturedCamp() {
  const handleRegisterClick = async () => {
    try {
      await fetch(`${API_BASE}/track-referral`, { method: "POST" });
    } catch (_) {
      // don't block the user if tracking fails
    }
    window.open(registrationUrl, "_blank", "noopener,noreferrer");
  };

  const chips = [
    "📅 Aug 4–7, 2026",
    "💰 $200–$280 sliding scale",
    "🍱 Lunch included",
    "📍 East Vancouver",
  ];

  return (
    <section
      style={{
        backgroundColor: "#FAFAF7",
        padding: "48px 24px",
        textAlign: "center",
      }}
    >
      <div style={{ maxWidth: "640px", margin: "0 auto" }}>
        <p
          style={{
            fontSize: "11px",
            fontWeight: 700,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "#2d6a4f",
            marginBottom: "8px",
          }}
        >
          ✦ Featured Camp
        </p>

        <div
          style={{
            backgroundColor: "white",
            borderRadius: "16px",
            padding: "28px 28px 24px",
            boxShadow: "0 2px 12px rgba(0,0,0,0.07)",
            border: "1.5px solid #d4edda",
            textAlign: "left",
          }}
        >
          {/* Header row */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              flexWrap: "wrap",
              gap: "8px",
              marginBottom: "12px",
            }}
          >
            <div>
              <h3
                style={{
                  fontSize: "20px",
                  fontWeight: 700,
                  color: "#1a3d2b",
                  margin: "0 0 4px",
                  fontFamily: "Fraunces, serif",
                }}
              >
                Middle-earth Day Camp
              </h3>
              <p style={{ fontSize: "13px", color: "#555", margin: 0 }}>
                by Eastside Story Guild · East Vancouver, BC
              </p>
            </div>
            <span
              style={{
                backgroundColor: "#e6f4ec",
                color: "#2d6a4f",
                fontSize: "12px",
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: "20px",
                whiteSpace: "nowrap",
              }}
            >
              Ages 7–13
            </span>
          </div>

          {/* Description */}
          <p
            style={{
              fontSize: "14px",
              color: "#444",
              lineHeight: "1.65",
              marginBottom: "16px",
            }}
          >
            Step into Middle-earth for four days of imaginative play, costumes,
            theatre games, and LARPing inspired by{" "}
            <em>The Hobbit</em> and <em>The Lord of the Rings</em>. Hobbit-themed
            lunch and snacks included.
          </p>

          {/* Detail chips */}
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              marginBottom: "20px",
            }}
          >
            {chips.map((chip) => (
              <span
                key={chip}
                style={{
                  backgroundColor: "#f0f7f4",
                  color: "#1a3d2b",
                  fontSize: "13px",
                  padding: "5px 12px",
                  borderRadius: "20px",
                  fontWeight: 500,
                }}
              >
                {chip}
              </span>
            ))}
          </div>

          {/* CTA + contact */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <button
              onClick={handleRegisterClick}
              style={{
                backgroundColor: "#2d6a4f",
                color: "white",
                padding: "10px 20px",
                borderRadius: "8px",
                fontSize: "14px",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
              }}
            >
              Register Now →
            </button>
            <a
              href="mailto:program@eastsidestoryguild.ca"
              style={{
                fontSize: "13px",
                color: "#2d6a4f",
                textDecoration: "none",
                fontWeight: 500,
              }}
            >
              ✉ program@eastsidestoryguild.ca
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
