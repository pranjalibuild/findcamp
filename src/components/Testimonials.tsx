const testimonials = [
  {
    initials: "KA",
    name: "K.A.",
    role: "Director, Data & Analytics",
    quote:
      "It's exactly what I have been searching for. Summer camps and after care can take so much of our time to figure out for the kids. Major time saver. Thank you!",
  },
  {
    initials: "MN",
    name: "M.N.",
    role: "Product Manager & Co-Founder",
    quote:
      "This is a great resource for parents that don't know where to start with searching for camps. It suggested a couple camps I wasn't aware of in my area. I'll be sharing this with other parents!",
  },
];

export default function Testimonials() {
  return (
    <section style={{ backgroundColor: "#f0f7f4", padding: "48px 24px", textAlign: "center" }}>
      <p style={{ fontSize: "12px", fontWeight: 600, letterSpacing: "0.1em", textTransform: "uppercase", color: "#2d6a4f", marginBottom: "8px" }}>
        What parents are saying
      </p>
      <h2 style={{ fontSize: "24px", fontWeight: 700, color: "#1a3d2b", marginBottom: "32px" }}>
        Parents tried it. Here's what happened.
      </h2>
      <div style={{ display: "flex", flexDirection: "column", gap: "16px", maxWidth: "600px", margin: "0 auto" }}>
        {testimonials.map((t, i) => (
          <div key={i} style={{ backgroundColor: "white", borderRadius: "12px", padding: "24px", textAlign: "left", boxShadow: "0 1px 4px rgba(0,0,0,0.06)" }}>
            <p style={{ fontSize: "15px", color: "#333", lineHeight: "1.6", marginBottom: "16px" }}>
              "{t.quote}"
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ width: "36px", height: "36px", borderRadius: "50%", backgroundColor: "#2d6a4f", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, flexShrink: 0 }}>
                {t.initials}
              </div>
              <div>
                <p style={{ fontWeight: 600, fontSize: "14px", color: "#1a3d2b", margin: 0 }}>{t.name}</p>
                <p style={{ fontSize: "12px", color: "#777", margin: 0 }}>{t.role}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
