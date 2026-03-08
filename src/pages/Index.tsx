import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Mail, Bell, TreePine, X } from "lucide-react";

type FormState = "idle" | "loading" | "success" | "error";

const Index = () => {
  const [formState, setFormState] = useState<FormState>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [email, setEmail] = useState("");
  const [zip, setZip] = useState("");
  const [radius, setRadius] = useState("10");
  const [age, setAge] = useState("");
  const [season, setSeason] = useState("");
  const [campTypes, setCampTypes] = useState<string[]>([]);
  const [campTypeOpen, setCampTypeOpen] = useState(false);
  const campTypeRef = useRef<HTMLDivElement>(null);

  const campTypeOptions = ["Sports", "Arts", "STEM", "Outdoors", "General", "Religious"];

  const toggleCampType = (type: string) => {
    setCampTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const removeCampType = (type: string) => {
    setCampTypes((prev) => prev.filter((t) => t !== type));
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (campTypeRef.current && !campTypeRef.current.contains(e.target as Node)) {
        setCampTypeOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormState("loading");
    setErrorMessage("");
    try {
      const res = await fetch("https://findcamp-production.up.railway.app/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          zip_or_postal: zip,
          radius_km: Number(radius),
          age: Number(age),
          season: season.toLowerCase(),
          camp_type: campTypes.join(", ").toLowerCase(),
        }),
      });
      if (res.status === 429) {
        setErrorMessage("You've used your 3 free searches. Check your inbox for your previous results!");
        setFormState("error");
      } else if (!res.ok) throw new Error("Request failed");
      else setFormState("success");
    } catch {
      setErrorMessage("Something went wrong. Please try again.");
      setFormState("error");
    }
  };

  const features = [
    {
      icon: "🔍",
      title: "Find",
      desc: "We search dozens of camp directories so you don't have to.",
    },
    {
      icon: "✉️",
      title: "Enquire",
      desc: "Get ready-to-send enquiry emails drafted for every match.",
    },
    {
      icon: "⏰",
      title: "Never Miss",
      desc: "Calendar reminders before registration opens.",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="py-4 px-6">
        <div className="max-w-2xl mx-auto flex items-center gap-2">
          <TreePine className="h-6 w-6 text-primary" />
          <span className="font-display text-xl text-foreground">Findcamp</span>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 px-6 pb-16">
        <div className="max-w-2xl mx-auto">
          <section className="pt-8 pb-10 text-center">
            <h1 className="font-display text-4xl sm:text-7xl font-bold text-foreground leading-tight mb-3">
              Find camps before they fill&nbsp;up.
            </h1>
            <p className="text-muted-foreground text-base sm:text-lg max-w-lg mx-auto leading-relaxed">
              Enter your postal code or zip and we'll find nearby camps, send ready-to-send enquiry emails, and remind you before registration opens. Free for 3 searches.
            </p>
          </section>

          {/* Form */}
          <Card className="p-6 sm:p-8 shadow-lg border-border/60">
            {formState === "success" ? (
              <div className="text-center py-8">
                <p className="text-2xl mb-2">🏕️</p>
                <h2 className="font-display text-xl text-foreground mb-2">Your results are on their way!</h2>
                <p className="text-muted-foreground">
                  Check your inbox — we've sent your camp list, ready-to-send enquiry emails, and calendar reminders.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="email" className="font-bold">Email</Label>
                  <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@email.com" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="zip" className="font-bold">Postal code or zip</Label>
                  <Input id="zip" required value={zip} onChange={(e) => setZip(e.target.value)} placeholder="V3E 2M1 or 90210" />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="radius" className="font-bold">How far are you willing to drive?</Label>
                  <Select value={radius} onValueChange={setRadius} required>
                    <SelectTrigger id="radius"><SelectValue placeholder="Select distance" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">Nearby ~5 km</SelectItem>
                      <SelectItem value="10">A short drive ~10 km</SelectItem>
                      <SelectItem value="20">Worth the trip ~20 km</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="age" className="font-bold">Child's age</Label>
                    <Input id="age" type="number" min={1} max={17} required value={age} onChange={(e) => setAge(e.target.value)} placeholder="8" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="season" className="font-bold">Season</Label>
                    <Select value={season} onValueChange={setSeason} required>
                      <SelectTrigger id="season"><SelectValue placeholder="Select" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Summer">Summer</SelectItem>
                        <SelectItem value="Spring">Spring</SelectItem>
                        <SelectItem value="Fall">Fall</SelectItem>
                        <SelectItem value="Winter">Winter</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="font-bold">Camp type</Label>
                  <div ref={campTypeRef} className="relative">
                    <div
                      onClick={() => setCampTypeOpen((o) => !o)}
                      className="flex min-h-10 w-full items-center gap-1 flex-wrap rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2"
                    >
                      {campTypes.length === 0 && (
                        <span className="text-muted-foreground">Select types</span>
                      )}
                      {campTypes.map((type) => (
                        <Badge key={type} variant="secondary" className="gap-1 pr-1">
                          {type}
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); removeCampType(type); }}
                            className="rounded-full hover:bg-muted-foreground/20 p-0.5"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                    {campTypeOpen && (
                      <div className="absolute z-50 mt-1 w-full rounded-md border border-border bg-popover p-1 shadow-md">
                        {campTypeOptions.map((type) => (
                          <div
                            key={type}
                            onClick={() => toggleCampType(type)}
                            className={`flex items-center gap-2 rounded-sm px-2 py-1.5 text-sm cursor-pointer hover:bg-accent hover:text-accent-foreground ${campTypes.includes(type) ? "bg-accent/50" : ""}`}
                          >
                            <div className={`h-4 w-4 rounded border flex items-center justify-center ${campTypes.includes(type) ? "bg-primary border-primary text-primary-foreground" : "border-input"}`}>
                              {campTypes.includes(type) && <span className="text-xs">✓</span>}
                            </div>
                            {type}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {formState === "error" && (
                  <p className="text-destructive text-sm">{errorMessage}</p>
                )}

                <Button type="submit" className="w-full text-base h-12" disabled={formState === "loading"}>
                  {formState === "loading" ? (
                    "🔍 Searching camps near you... this takes about 20 seconds"
                  ) : (
                    "Find My Camps →"
                  )}
                </Button>
              </form>
            )}
          </Card>

          {/* Features */}
          <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-12">
            {features.map((f) => (
              <Card key={f.title} className="p-5 text-center border-border/60">
                <div className="text-4xl mb-3">
                  {f.icon}
                </div>
                <h3 className="font-display text-lg text-foreground mb-1">{f.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
              </Card>
            ))}
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-6 text-center text-muted-foreground text-sm">
        Built by a parent, for parents · <a href="https://findcamp.co" className="underline hover:text-foreground transition-colors">findcamp.co</a>
      </footer>
    </div>
  );
};

export default Index;
