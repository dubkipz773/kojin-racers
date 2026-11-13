(function (global) {
  const MAKES = [
    ["hyuandai", "Hyundai"], ["hyundai", "Hyundai"], ["honda", "Honda"],
    ["toyota", "Toyota"], ["ford", "Ford"], ["chevy", "Chevrolet"], ["chevrolet", "Chevrolet"],
    ["mazda", "Mazda"], ["scion", "Scion"], ["nissan", "Nissan"], ["subaru", "Subaru"],
    ["kia", "Kia"], ["bmw", "BMW"], ["volkswagen", "Volkswagen"], ["vw", "Volkswagen"],
    ["jeep", "Jeep"], ["dodge", "Dodge"], ["ram", "Ram"], ["gmc", "GMC"], ["lexus", "Lexus"]
  ];

  function normalizeText(s) {
    return (s || "").replace(/\s+/g, " ").trim();
  }

  function extractName(text) {
    const m = text.match(/\b(?:my name is|this is|i'?m)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i);
    return m ? m[1] : "";
  }

  function extractPhone(text) {
    const m = text.match(/(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})/);
    return m ? m[0].replace(/\s+/g, " ").trim() : "";
  }

  function normalizeModel(make, model) {
    if (/^xd$/i.test(model) && /scion/i.test(make)) return "xD";
    if (/^crv$/i.test(model)) return "CR-V";
    if (/^tucson$/i.test(model)) return "Tucson";
    if (/^expedition$/i.test(model)) return "Expedition";
    if (/^civic$/i.test(model)) return "Civic";
    if (/^sonata$/i.test(model)) return "Sonata";
    return model;
  }

  function canonMake(raw) {
    const makeRaw = raw.toLowerCase();
    for (const [k, v] of MAKES) {
      if (makeRaw === k || makeRaw.startsWith(k)) return v;
    }
    return raw.charAt(0).toUpperCase() + raw.slice(1);
  }

  function extractVehicle(text) {
    const lower = text.toLowerCase();

    if (/rx[-\s]?7|rx\s*seven|fdrx7/.test(lower)) {
      const yearM = text.match(/(19\d{2}|20\d{2})/);
      let year = yearM ? yearM[1] : "";
      if (/fd/.test(lower) && !year) year = "1999";
      return normalizeText((year + " Mazda RX-7").trim());
    }

    const fromYear = text.match(/\b(scion|honda|toyota|ford|hyundai|hyuandai|mazda|nissan|subaru)\s+([A-Za-z0-9-]+)\s+from\s+(19\d{2}|20\d{2})/i);
    if (fromYear) {
      const make = canonMake(fromYear[1]);
      return fromYear[3] + " " + make + " " + normalizeModel(make, fromYear[2]);
    }

    const yearMake = text.match(/(19\d{2}|20\d{2})\s+([A-Za-z]+)\s+([A-Za-z0-9][A-Za-z0-9-]*)/);
    if (yearMake) {
      const make = canonMake(yearMake[2]);
      let model = yearMake[3];
      if (/^(that|has|the|a|an|and|with)$/i.test(model)) {
        const alt = text.match(/\b(scion|honda|toyota|ford|hyundai|hyuandai|mazda|nissan)\s+([A-Za-z0-9-]+)/i);
        if (alt) {
          const m2 = canonMake(alt[1]);
          return yearMake[1] + " " + m2 + " " + normalizeModel(m2, alt[2]);
        }
        return yearMake[1] + " " + make;
      }
      return yearMake[1] + " " + make + " " + normalizeModel(make, model);
    }

    return "";
  }

  function extractService(text) {
    const l = text.toLowerCase();
    if (/apex\s*seal|rebuild\s+my\s+motor|rotary|engine rebuild/.test(l)) return "Rotary / apex seal engine rebuild quote";
    if (/wheel\s*bearing|how to do wheel bearings/.test(l)) return "Wheel bearing service / how-to question";
    if (/alignment/.test(l)) return "Wheel alignment";
    if (/oil\s*change|drain\s*plug|oil\s*filter/.test(l)) return "Oil change / oil system check";
    if (/catalytic|exhaust|flange|band\s*clamp|\bweld\b/.test(l)) return "Exhaust pipe / flange repair";
    if (/body\s*damage|crashed|front left panel/.test(l)) return "Body repair — panel damage";
    if (/check\s*engine|engine light|stops working|\bcel\b/.test(l)) return "Check-engine / drivability diagnosis";
    if (/squeaky\s+motor|engine noise|banging sound|bang.*shut/.test(l)) return "Engine / noise diagnosis";
    if (/brake\s*pads?/.test(l) && !/grind|soft\s*pedal|can'?t stop/.test(l)) return "Brake pad replacement";
    if (/brake\s*rotor|trailing\s*arm/.test(l)) return "Brake rotors / related suspension";
    if (/brake|squeeky brake|squeaky brake/.test(l)) return "Brake inspection";
    return "";
  }

  function urgency(text, service) {
    const l = text.toLowerCase();
    const critical =
      (/(grind|grinding)/.test(l) && /soft|spongy/.test(l) && /pedal|brake/.test(l)) ||
      /can'?t stop|won'?t stop|no brakes|unable to stop/.test(l) ||
      (/pulling hard|pulls hard/.test(l) && /brake/.test(l)) ||
      /brake fluid leak|leaking brake fluid/.test(l) ||
      /don'?t drive|do not drive|unsafe to drive|\btow\b/.test(l);
    if (critical) return "CRITICAL — SAFETY";
    if (/pipe separated|separated from the flange|dragging|fumes inside|exhaust fumes/.test(l)) return "HIGH — INSPECT";
    if (/stops working|car stops|limp|won'?t go/.test(l) && /engine light|check engine|shift/.test(l)) return "HIGH";
    if (/brake/.test(l) || /brake/.test((service || "").toLowerCase())) return "HIGH";
    return "NORMAL";
  }

  function missingInfo(vehicle, name, phone, text) {
    const miss = [];
    if (!name) miss.push("customer name");
    if (!vehicle) miss.push("vehicle year/make/model");
    if (!/monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today|\d\s*(am|pm)|prefer|available/.test(text.toLowerCase())) {
      miss.push("preferred appointment time");
    }
    return miss.length ? miss.join("; ") : "None — verify manually";
  }

  function nextAction(urg, service, vehicle) {
    if (urg === "CRITICAL — SAFETY") return "URGENT: Do not drive. Contact customer promptly; recommend tow; technician assess.";
    if (urg.startsWith("HIGH")) return "Contact promptly. Inspect " + (service || "concern") + " on " + (vehicle || "vehicle") + " before advising driveability.";
    return "Review message, confirm details, and schedule " + (service || "service") + " for " + (vehicle || "vehicle") + ".";
  }

  function buildDraft(opts) {
    const who = opts.name ? (" " + opts.name) : "";
    const veh = opts.vehicle ? (" about your " + opts.vehicle) : "";
    const svc = opts.service ? (" (" + opts.service + ")") : "";
    let body;
    if (opts.urgency === "CRITICAL — SAFETY") {
      body = "Hi" + who + " — thanks for reaching out" + veh + svc + ". This sounds like a safety issue. Please don’t drive the vehicle; arrange a tow to the shop if you can. Reply with a good time for us to call.";
    } else if (opts.urgency.startsWith("HIGH")) {
      body = "Hi" + who + " — thanks for reaching out" + veh + svc + ". We’d like to take a look soon.";
      if (/brake/i.test(opts.service || opts.text)) body += " We’ll inspect before advising whether it’s okay to keep driving.";
      if (/exhaust|flange/i.test(opts.service || opts.text)) body += " If the pipe is dragging or you smell fumes inside, don’t drive it and arrange a tow.";
    } else {
      body = "Hi" + who + " — thanks for reaching out" + veh + svc + ".";
    }
    if (opts.missing && opts.missing !== "None — verify manually") {
      const ask = opts.missing
        .replace(/customer name/g, "your name")
        .replace(/vehicle year\/make\/model/g, "the year, make, and model")
        .replace(/preferred appointment time/g, "what days or times work for you");
      body += " Could you share " + ask + "?";
    } else {
      body += " What days or times work for a call or drop-off?";
    }
    body += " This is a draft for the shop to review; it has not been sent.";
    return body.replace(/column\s+[A-Z]/gi, "").replace(/\s{2,}/g, " ").trim();
  }

  function analyze(raw) {
    const text = normalizeText(raw);
    const customer = extractName(text);
    const phone = extractPhone(text);
    const vehicle = extractVehicle(text);
    const service = extractService(text);
    const urg = urgency(text, service);
    const missing = missingInfo(vehicle, customer, phone, text);
    const next = nextAction(urg, service, vehicle);
    const draft = buildDraft({ name: customer, vehicle, service, urgency: urg, missing, text });
    return {
      customer: customer || "(unknown)",
      phone,
      vehicle: vehicle || "(need year/make/model)",
      service: service || "(need service details)",
      urgency: urg,
      missing,
      nextAction: next,
      draft,
      summary: urg + ": " + (service || "manual review") + " · " + (vehicle || "vehicle TBD"),
      original: text,
      status: "New",
      automation: "Draft prepared — review required; not sent",
      date: new Date().toISOString().slice(0, 10)
    };
  }

  global.ShopLeadExtract = { analyze };
})(window);
