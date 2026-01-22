import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import filedialog

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_FILE = "3DPrintCalc_Database.json"
LANG_FILE = "translations.json"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("3DPrintCalc Pro v2")
        self.geometry("1300x950")
        
        self.lang = "ITA"
        self.translations = self.load_translations()
        self.db = self.load_db()
        
        self.mod_phases = []
        self.post_phases = []
        self.consumables = []
        
        self.current_tab = "calc"
        self.nav_buttons = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1b26")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="3DPrintCalc", font=("Arial", 24, "bold"), text_color="#7aa2f7").pack(pady=40)

        self.create_nav_button("nav_calc", "calc")
        self.create_nav_button("nav_printers", "printers")
        self.create_nav_button("nav_filaments", "filaments")

        self.btn_lang = ctk.CTkButton(self.sidebar, text=self.translations[self.lang]["lang_btn"], 
                                      fg_color="#24283b", command=self.toggle_language)
        self.btn_lang.pack(side="bottom", pady=20, padx=20, fill="x")

        # --- MAIN FRAME ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#24283b")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.tabs = {}
        self.setup_calc_tab()
        self.setup_printer_tab()
        self.setup_filament_tab()
        self.show_tab("calc")

    def load_translations(self):
        if os.path.exists(LANG_FILE):
            with open(LANG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        return {"ITA": {"nav_calc": "Preventivo", "lang_btn": "ITA"}}

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f: return json.load(f)
            except: pass
        return {"printers": [], "filaments": [], "electricity_cost": 0.25}

    def save_db(self):
        with open(DB_FILE, "w") as f: json.dump(self.db, f, indent=4)

    def toggle_language(self):
        self.lang = "ENG" if self.lang == "ITA" else "ITA"
        self.btn_lang.configure(text=self.translations[self.lang]["lang_btn"])
        self.show_tab(self.current_tab)

    def create_nav_button(self, lang_key, tab_name):
        btn = ctk.CTkButton(self.sidebar, text=self.translations[self.lang][lang_key], 
                            height=45, corner_radius=0, fg_color="transparent", 
                            font=("Arial", 14, "bold"), command=lambda: self.show_tab(tab_name))
        btn.pack(pady=2, fill="x")
        self.nav_buttons[tab_name] = btn

    def show_tab(self, name):
        self.current_tab = name
        for t in self.tabs.values(): t.pack_forget()
        for k, b in self.nav_buttons.items():
            b.configure(fg_color="#7aa2f7" if k == name else "transparent", 
                        text_color="black" if k == name else "white",
                        text=self.translations[self.lang][f"nav_{k}"])
        self.tabs[name].pack(fill="both", expand=True)
        if name == "printers": self.render_printer_list()
        elif name == "filaments": self.render_filament_list()
        elif name == "calc": self.refresh_calc_ui()

    def get_fil_name(self, f):
        name = f"{f['brand']} {f['material']}"
        if f.get('color'): name += f" ({f['color']})"
        return name

    # --- TAB CALCOLO ---
    def setup_calc_tab(self):
        self.tabs["calc"] = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")

    def refresh_calc_ui(self):
        tab = self.tabs["calc"]; [w.destroy() for w in tab.winfo_children()]
        t = self.translations[self.lang]
        ctk.CTkLabel(tab, text=t["header_calc"], font=("Arial", 28, "bold")).pack(pady=20)
        container = ctk.CTkFrame(tab, fg_color="transparent"); container.pack(fill="x")
        
        # Colonna Tecnica
        l_col = ctk.CTkFrame(container, corner_radius=10); l_col.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(l_col, text=t["setup_stampa"], font=("Arial", 16, "bold"), text_color="#bb9af7").pack(pady=10)
        self.color_preview = ctk.CTkFrame(l_col, width=30, height=30, corner_radius=15, border_width=2, border_color="white"); self.color_preview.pack()

        p_vals = [p["name"] for p in self.db["printers"]] or ["---"]
        f_vals = [self.get_fil_name(f) for f in self.db["filaments"]] or ["---"]
        self.opt_p = ctk.CTkOptionMenu(l_col, values=p_vals); self.opt_p.pack(pady=5)
        self.opt_f = ctk.CTkOptionMenu(l_col, values=f_vals, command=self.update_color_preview); self.opt_f.pack(pady=5)
        self.ent_g = self.create_ui_field(l_col, t["grams"], "50")
        self.ent_h = self.create_ui_field(l_col, t["hours_print"], "2")

        # Colonna Business
        r_col = ctk.CTkFrame(container, corner_radius=10); r_col.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(r_col, text=t["business"], font=("Arial", 16, "bold"), text_color="#ff9e64").pack(pady=10)
        self.ent_markup = self.create_ui_field(r_col, t["markup"], "50")
        self.ent_iva = self.create_ui_field(r_col, t["iva"], "22")
        self.ent_elec = self.create_ui_field(r_col, t["elec_rate"], str(self.db.get("electricity_cost", 0.25)))

        # Sezioni Lavorazioni
        f_container = ctk.CTkFrame(tab, fg_color="#1a1b26", corner_radius=15); f_container.pack(fill="x", padx=10, pady=20)
        self.create_fluid_section(f_container, t["mod_title"], self.mod_phases)
        self.create_fluid_section(f_container, t["post_title"], self.post_phases)
        self.create_fluid_section(f_container, t["cons_title"], self.consumables)

        ctk.CTkButton(tab, text=t["btn_calc"], height=55, fg_color="#9ece6a", text_color="black", font=("Arial", 20, "bold"), command=self.calculate).pack(pady=20, padx=100, fill="x")
        self.lbl_res = ctk.CTkLabel(tab, text="€ 0.00", font=("Arial", 44, "bold"), text_color="#9ece6a"); self.lbl_res.pack()
        self.lbl_detail = ctk.CTkLabel(tab, text="", font=("Arial", 13), text_color="#a9b1d6", justify="center"); self.lbl_detail.pack(pady=10)

        act_f = ctk.CTkFrame(tab, fg_color="transparent"); act_f.pack(pady=20)
        self.btn_reg = ctk.CTkButton(act_f, text=t["btn_reg"], state="disabled", command=self.register_print, fg_color="#7aa2f7", text_color="black"); self.btn_reg.pack(side="left", padx=10)
        self.btn_rep = ctk.CTkButton(act_f, text=t["btn_rep"], state="disabled", command=self.generate_report, fg_color="#bb9af7", text_color="black"); self.btn_rep.pack(side="left", padx=10)

    def create_fluid_section(self, master, title, list_obj):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(side="left", expand=True, fill="both", padx=5, pady=10)
        ctk.CTkLabel(frame, text=title, font=("Arial", 13, "bold")).pack()
        add_f = ctk.CTkFrame(frame, fg_color="transparent"); add_f.pack(fill="x", pady=5)
        e_n = ctk.CTkEntry(add_f, placeholder_text="Nome", height=28); e_n.pack(side="left", expand=True, fill="x", padx=2)
        e_c = ctk.CTkEntry(add_f, placeholder_text="€", width=50, height=28); e_c.pack(side="left", padx=2)
        list_f = ctk.CTkFrame(frame, fg_color="transparent"); list_f.pack(fill="x")
        def render_list():
            for w in list_f.winfo_children(): w.destroy()
            for i, item in enumerate(list_obj):
                row = ctk.CTkFrame(list_f, fg_color="#24283b"); row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"{item['name']} (€{item['cost']:.2f})", font=("Arial", 10)).pack(side="left", padx=5)
                ctk.CTkButton(row, text="x", width=15, height=15, fg_color="#f7768e", command=lambda idx=i: [list_obj.pop(idx), render_list()]).pack(side="right", padx=2)
        def add_item():
            try:
                val = float(e_c.get().replace(',','.'))
                if e_n.get(): list_obj.append({"name": e_n.get(), "cost": val}); e_n.delete(0, 'end'); e_c.delete(0, 'end'); render_list()
            except: pass
        ctk.CTkButton(add_f, text="+", width=30, height=28, command=add_item).pack(side="left"); render_list()

    def update_color_preview(self, choice):
        f = next((x for x in self.db["filaments"] if self.get_fil_name(x) == choice), None)
        if f: self.color_preview.configure(fg_color=f.get("hex", "#ffffff"))

    def calculate(self):
        t = self.translations[self.lang]
        try:
            p = next(x for x in self.db["printers"] if x["name"] == self.opt_p.get())
            f = next(x for x in self.db["filaments"] if self.get_fil_name(x) == self.opt_f.get())
            g, h = float(self.ent_g.get().replace(',','.')), float(self.ent_h.get().replace(',','.'))
            e_rate = float(self.ent_elec.get().replace(',','.'))
            markup_p = float(self.ent_markup.get().replace(',','.'))
            iva_p = float(self.ent_iva.get().replace(',','.'))

            c_mat = (f['price'] / f['weight']) * g
            c_en = (p['watt'] / 1000) * h * e_rate
            c_wear_b = (p['base_cost'] / p['life']) * h
            c_wear_p = sum((cp['cost'] / cp['life']) * h for cp in p.get('components', []))
            c_cons = sum(c['cost'] for c in self.consumables)
            
            tech = c_mat + c_en + c_wear_b + c_wear_p + c_cons
            labor = sum(ph['cost'] for ph in self.mod_phases + self.post_phases)
            
            sub = (tech + labor) * (1 + markup_p/100)
            final = sub * (1 + iva_p/100)
            
            self.lbl_res.configure(text=f"€ {final:.2f}")
            self.lbl_detail.configure(text=f"Mat: €{c_mat:.2f} | En: €{c_en:.2f} | Usura: €{c_wear_b+c_wear_p:.2f} | Cons: €{c_cons:.2f}\nTech Total: €{tech:.2f} | Labor: €{labor:.2f}")
            
            self.last_calc_data = {"p":p['name'], "f":self.get_fil_name(f), "g":g, "h":h, "tot":final, "c_mat":c_mat, "c_en":c_en, "c_wear_b":c_wear_b, "c_wear_p":c_wear_p, "c_cons":c_cons, "tech":tech, "labor":labor, "markup_p":markup_p, "iva_p":iva_p}
            self.db["electricity_cost"] = e_rate; self.save_db()
            self.btn_reg.configure(state="normal"); self.btn_rep.configure(state="normal")
        except: self.lbl_res.configure(text="Error", text_color="red")

    def register_print(self):
        d = self.last_calc_data
        f = next(x for x in self.db["filaments"] if self.get_fil_name(x) == d["f"])
        f["rem_weight"] -= d["g"]
        p = next(x for x in self.db["printers"] if x["name"] == d["p"])
        p["used_hours"] += d["h"]; [cp.update({"used_hours": cp["used_hours"] + d["h"]}) for cp in p.get("components", [])]
        self.save_db(); self.btn_reg.configure(text=self.translations[self.lang]["save_success"], state="disabled")

    def generate_report(self):
        d = self.last_calc_data
        mod_s = "".join([f"  - {ph['name']}: €{ph['cost']:.2f}\n" for ph in self.mod_phases]) or "  - Nessuna\n"
        post_s = "".join([f"  - {ph['name']}: €{ph['cost']:.2f}\n" for ph in self.post_phases]) or "  - Nessuna\n"
        cons_s = "".join([f"  - {c['name']}: €{c['cost']:.2f}\n" for c in self.consumables]) or "  - Nessuno\n"
        
        report = f"""==================================================
           REPORT PREVENTIVO STAMPA 3D
==================================================
STAMPANTE: {d['p']}
MATERIALE: {d['f']} ({d['g']}g)
TEMPO:     {d['h']} h
--------------------------------------------------
COSTI TECNICI (VIVI):
  Materiale: € {d['c_mat']:.2f} | Energia: € {d['c_en']:.2f}
  Usura Struttura: € {d['c_wear_b']:.2f} | Usura Pezzi: € {d['c_wear_p']:.2f}
  Consumabili Extra:
{cons_s}
  TOTALE TECNICO: € {d['tech']:.2f}
--------------------------------------------------
LAVORO E MANODOPERA:
  MODELLAZIONE:
{mod_s}  POST-PRODUZIONE:
{post_s}  TOTALE LAVORO: € {d['labor']:.2f}
--------------------------------------------------
RIEPILOGO:
  Rincaro ({int(d['markup_p'])}%): € {( (d['tech']+d['labor']) * d['markup_p']/100 ):.2f}
  IVA ({int(d['iva_p'])}%):     € {( d['tot'] - (d['tot']/(1+d['iva_p']/100)) ):.2f}
  TOTALE CLIENTE: € {d['tot']:.2f}
=================================================="""
        fn = f"Preventivo_{datetime.now().strftime('%H%M%S')}.txt"
        with open(fn, "w", encoding="utf-8") as f: f.write(report)
        os.startfile(fn)

    # --- TABS GESTIONE ---
    def setup_printer_tab(self):
        self.tabs["printers"] = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.p_list_view = ctk.CTkFrame(self.tabs["printers"], fg_color="transparent")
        self.p_edit_view = ctk.CTkScrollableFrame(self.tabs["printers"], fg_color="transparent")

    def render_printer_list(self):
        t = self.translations[self.lang]; self.p_edit_view.pack_forget(); self.p_list_view.pack(fill="both", expand=True)
        for w in self.p_list_view.winfo_children(): w.destroy()
        ctk.CTkButton(self.p_list_view, text=t["btn_add_p"], command=self.add_printer, fg_color="#7aa2f7", text_color="black").pack(pady=20)
        scroll = ctk.CTkScrollableFrame(self.p_list_view, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        for p in self.db["printers"]:
            card = ctk.CTkFrame(scroll, corner_radius=12, fg_color="#1a1b26"); card.pack(fill="x", pady=8, padx=15)
            ctk.CTkLabel(card, text=f"{p['name']} ({p.get('used_hours',0):.1f}h)").pack(side="left", padx=15, pady=15)
            ctk.CTkButton(card, text=t["config"], width=100, command=lambda x=p: self.open_p_edit(x), fg_color="#24283b").pack(side="right", padx=15)

    def open_p_edit(self, p):
        self.current_editing_obj = p; self.p_list_view.pack_forget(); self.p_edit_view.pack(fill="both", expand=True); self.refresh_p_edit()

    def refresh_p_edit(self):
        [w.destroy() for w in self.p_edit_view.winfo_children()]
        p, t = self.current_editing_obj, self.translations[self.lang]
        ctk.CTkButton(self.p_edit_view, text=t["back"], command=self.render_printer_list, width=100).pack(pady=10)
        self.en_p_n = self.create_ui_field(self.p_edit_view, "Nome", p["name"])
        self.en_p_c = self.create_ui_field(self.p_edit_view, "Costo €", p["base_cost"])
        self.en_p_l = self.create_ui_field(self.p_edit_view, "Vita h", p["life"])
        self.en_p_w = self.create_ui_field(self.p_edit_view, "Watt", p["watt"])
        ctk.CTkButton(self.p_edit_view, text=t["save"], fg_color="#9ece6a", text_color="black", command=self.save_p).pack(pady=10)
        ctk.CTkButton(self.p_edit_view, text=t["delete"], fg_color="red", command=self.del_p).pack(pady=5)
        ctk.CTkLabel(self.p_edit_view, text=t["wear_cost"], font=("Arial", 20, "bold")).pack(pady=20)
        add_f = ctk.CTkFrame(self.p_edit_view, fg_color="#1a1b26", corner_radius=10); add_f.pack(fill="x", padx=20, pady=10)
        ni_n = ctk.CTkEntry(add_f, placeholder_text=t["part_name"]); ni_n.grid(row=0, column=0, padx=10, pady=20)
        ni_c = ctk.CTkEntry(add_f, placeholder_text=t["part_cost"], width=80); ni_c.grid(row=0, column=1, padx=5)
        ni_l = ctk.CTkEntry(add_f, placeholder_text=t["part_life"], width=80); ni_l.grid(row=0, column=2, padx=5)
        def add_p():
            try: p['components'].append({"name": ni_n.get(), "cost": float(ni_c.get()), "life": float(ni_l.get()), "used_hours": 0}); self.save_db(); self.refresh_p_edit()
            except: pass
        ctk.CTkButton(add_f, text="+", width=40, command=add_p, fg_color="#7aa2f7", text_color="black").grid(row=0, column=3, padx=10)
        for i, c in enumerate(p.get("components", [])):
            cf = ctk.CTkFrame(self.p_edit_view, fg_color="#24283b", corner_radius=8); cf.pack(fill="x", pady=2, padx=20)
            ctk.CTkLabel(cf, text=f"{c['name']} (€{c['cost']}) - {c['used_hours']:.1f}/{c['life']}h").pack(side="left", padx=15, pady=10)
            ctk.CTkButton(cf, text="X", width=30, fg_color="red", command=lambda idx=i: [p['components'].pop(idx), self.save_db(), self.refresh_p_edit()]).pack(side="right", padx=15)

    def save_p(self): self.current_editing_obj.update({"name":self.en_p_n.get(),"base_cost":float(self.en_p_c.get()),"life":float(self.en_p_l.get()),"watt":float(self.en_p_w.get())}); self.save_db(); self.render_printer_list()
    def add_printer(self): self.db["printers"].append({"name":"Nuova","base_cost":300,"life":5000,"used_hours":0,"watt":150,"components":[]}); self.save_db(); self.render_printer_list()
    def del_p(self): self.db["printers"].remove(self.current_editing_obj); self.save_db(); self.render_printer_list()

    def setup_filament_tab(self):
        self.tabs["filaments"] = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.f_list_view = ctk.CTkFrame(self.tabs["filaments"], fg_color="transparent")
        self.f_edit_view = ctk.CTkScrollableFrame(self.tabs["filaments"], fg_color="transparent")

    def render_filament_list(self):
        t = self.translations[self.lang]; self.f_edit_view.pack_forget(); self.f_list_view.pack(fill="both", expand=True)
        for w in self.f_list_view.winfo_children(): w.destroy()
        ctk.CTkButton(self.f_list_view, text=t["btn_add_f"], command=self.add_fil, fg_color="#7aa2f7", text_color="black").pack(pady=20)
        for f in self.db["filaments"]:
            fr = ctk.CTkFrame(self.f_list_view, fg_color="#1a1b26"); fr.pack(fill="x", pady=5, padx=10)
            ctk.CTkFrame(fr, width=20, height=20, corner_radius=10, fg_color=f.get("hex","#fff")).pack(side="left", padx=15)
            ctk.CTkLabel(fr, text=self.get_fil_name(f)).pack(side="left", pady=15)
            ctk.CTkButton(fr, text=t["config"], width=80, command=lambda x=f: self.open_f_edit(x), fg_color="#24283b").pack(side="right", padx=15)

    def open_f_edit(self, f): self.current_editing_obj = f; self.f_list_view.pack_forget(); self.f_edit_view.pack(fill="both", expand=True); self.refresh_f_edit()

    def refresh_f_edit(self):
        [w.destroy() for w in self.f_edit_view.winfo_children()]
        f, t = self.current_editing_obj, self.translations[self.lang]
        ctk.CTkButton(self.f_edit_view, text=t["back"], command=self.render_filament_list, width=100).pack(pady=10)
        self.ef_b = self.create_ui_field(self.f_edit_view, t["f_brand"], f["brand"])
        self.ef_m = self.create_ui_field(self.f_edit_view, t["f_mat"], f["material"])
        self.ef_c = self.create_ui_field(self.f_edit_view, t["f_col"], f.get("color",""))
        self.ef_h = self.create_ui_field(self.f_edit_view, t["f_hex"], f.get("hex","#ffffff"))
        self.ef_p = self.create_ui_field(self.f_edit_view, t["f_pri"], f["price"])
        self.ef_w = self.create_ui_field(self.f_edit_view, t["f_wei"], f["weight"])
        self.ef_r = self.create_ui_field(self.f_edit_view, t["f_rem"], f["rem_weight"])
        ctk.CTkButton(self.f_edit_view, text=t["save"], fg_color="#9ece6a", text_color="black", command=self.save_f).pack(pady=10)
        ctk.CTkButton(self.f_edit_view, text=t["delete"], fg_color="red", command=lambda: [self.db["filaments"].remove(f), self.save_db(), self.render_filament_list()]).pack()

    def save_f(self):
        self.current_editing_obj.update({"brand":self.ef_b.get(),"material":self.ef_m.get(),"color":self.ef_c.get(),"hex":self.ef_h.get(),"price":float(self.ef_p.get().replace(',','.')),"weight":float(self.ef_w.get().replace(',','.')),"rem_weight":float(self.ef_r.get().replace(',','.'))})
        self.save_db(); self.render_filament_list()

    def add_fil(self): self.db["filaments"].append({"brand":"Nuovo","material":"PLA","color":"","hex":"#ffffff","price":25,"weight":1000,"rem_weight":1000}); self.save_db(); self.render_filament_list()

    def create_ui_field(self, master, label, default):
        f = ctk.CTkFrame(master, fg_color="transparent"); f.pack(fill="x", pady=4, padx=20)
        ctk.CTkLabel(f, text=label, width=150, anchor="w", font=("Arial", 14)).pack(side="left")
        e = ctk.CTkEntry(f, width=200); e.insert(0, str(default)); e.pack(side="right"); return e

if __name__ == "__main__":
    App().mainloop()