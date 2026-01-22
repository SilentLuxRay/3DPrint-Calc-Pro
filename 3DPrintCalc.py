import customtkinter as ctk
import json
import os
from datetime import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_FILE = "3DPrintCalc_Database.json"
LANG_FILE = "translations.json"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("3DPrintCalc Pro")
        self.geometry("1150x850")
        
        self.lang = "ITA"
        self.translations = self.load_translations()
        self.db = self.load_db()
        
        self.current_tab = "calc"
        self.current_editing_obj = None 
        self.last_calc_data = None 
        self.nav_buttons = {} 

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR PULITA (SOLO TESTO) ---
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
        
        self.color_preview = ctk.CTkFrame(l_col, width=30, height=30, corner_radius=15, border_width=2, border_color="white")
        self.color_preview.pack(pady=5)

        p_vals = [p["name"] for p in self.db["printers"]] or ["---"]
        f_vals = [f"{f['brand']} {f['material']} ({f.get('color','')})" for f in self.db["filaments"]] or ["---"]
        
        self.opt_p = ctk.CTkOptionMenu(l_col, values=p_vals); self.opt_p.pack(pady=5)
        self.opt_f = ctk.CTkOptionMenu(l_col, values=f_vals, command=self.update_color_preview); self.opt_f.pack(pady=5)
        self.ent_g = self.create_ui_field(l_col, t["grams"], "50")
        self.ent_h = self.create_ui_field(l_col, t["hours_print"], "2")

        # Colonna Business
        r_col = ctk.CTkFrame(container, corner_radius=10); r_col.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        ctk.CTkLabel(r_col, text=t["business"], font=("Arial", 16, "bold"), text_color="#ff9e64").pack(pady=10)
        self.ent_mod = self.create_ui_field(r_col, t["modelling"], "0")
        self.ent_post = self.create_ui_field(r_col, t["post_prod"], "0")
        self.ent_rate = self.create_ui_field(r_col, t["rate"], "20")
        self.ent_markup = self.create_ui_field(r_col, t["markup"], "50")
        self.ent_iva = self.create_ui_field(r_col, t["iva"], "22")
        self.ent_elec = self.create_ui_field(r_col, t["elec_rate"], str(self.db.get("electricity_cost", 0.25)))

        ctk.CTkButton(tab, text=t["btn_calc"], height=50, fg_color="#9ece6a", text_color="black", font=("Arial", 16, "bold"), command=self.calculate).pack(pady=25)
        self.lbl_res = ctk.CTkLabel(tab, text="€ 0.00", font=("Arial", 44, "bold"), text_color="#9ece6a"); self.lbl_res.pack()
        self.lbl_detail = ctk.CTkLabel(tab, text="", font=("Arial", 13), text_color="#a9b1d6", justify="center"); self.lbl_detail.pack(pady=10)

        f_btns = ctk.CTkFrame(tab, fg_color="transparent"); f_btns.pack(pady=20)
        self.btn_reg = ctk.CTkButton(f_btns, text=t["btn_reg"], state="disabled", command=self.register_print, fg_color="#7aa2f7", text_color="black"); self.btn_reg.pack(side="left", padx=10)
        self.btn_rep = ctk.CTkButton(f_btns, text=t["btn_rep"], state="disabled", command=self.generate_report, fg_color="#bb9af7", text_color="black"); self.btn_rep.pack(side="left", padx=10)

    def update_color_preview(self, choice):
        f = next((x for x in self.db["filaments"] if f"{x['brand']} {x['material']} ({x.get('color','')})" == choice), None)
        if f: self.color_preview.configure(fg_color=f.get("hex", "#ffffff"))

    def calculate(self):
        t = self.translations[self.lang]
        try:
            p = next(x for x in self.db["printers"] if x["name"] == self.opt_p.get())
            f = next(x for x in self.db["filaments"] if f"{x['brand']} {x['material']} ({x.get('color','')})" == self.opt_f.get())
            g = float(self.ent_g.get().replace(',','.'))
            h = float(self.ent_h.get().replace(',','.'))
            e_rate = float(self.ent_elec.get().replace(',','.'))
            
            c_mat = (f['price'] / f['weight']) * g
            c_en = (p['watt'] / 1000) * h * e_rate
            c_wear_body = (p['base_cost'] / p['life']) * h
            c_wear_parts = sum((cp['cost'] / cp['life']) * h for cp in p.get('components', []))
            total_wear = c_wear_body + c_wear_parts
            
            tech_cost = c_mat + c_en + total_wear
            labor = (float(self.ent_mod.get().replace(',','.')) + float(self.ent_post.get().replace(',','.'))) * float(self.ent_rate.get().replace(',','.'))
            final = (tech_cost + labor) * (1 + float(self.ent_markup.get().replace(',','.'))/100) * (1 + float(self.ent_iva.get().replace(',','.'))/100)
            
            self.lbl_res.configure(text=f"€ {final:.2f}")
            self.lbl_detail.configure(text=f"{t['mat_cost']}: €{c_mat:.2f} | {t['elec_cost']}: €{c_en:.2f} | {t['wear_cost']}: €{total_wear:.2f}\n{t['labor_cost']}: €{labor:.2f} | {t['tech_total']}: €{tech_cost:.2f}")
            
            self.last_calc_data = {"p": p['name'], "f": self.opt_f.get(), "g": g, "h": h, "tot": final}
            self.db["electricity_cost"] = e_rate; self.save_db()
            self.btn_reg.configure(state="normal"); self.btn_rep.configure(state="normal")
        except: self.lbl_res.configure(text="Error", text_color="red")

    def register_print(self):
        d = self.last_calc_data
        f = next(x for x in self.db["filaments"] if f"{x['brand']} {x['material']} ({x.get('color','')})" == d["f"])
        f["rem_weight"] -= d["g"]
        p = next(x for x in self.db["printers"] if x["name"] == d["p"])
        p["used_hours"] += d["h"]
        for cp in p.get("components", []): cp["used_hours"] += d["h"]
        self.save_db(); self.btn_reg.configure(text=self.translations[self.lang]["save_success"], state="disabled")

    # --- TAB STAMPANTI ---
    def setup_printer_tab(self):
        self.tabs["printers"] = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.p_list_view = ctk.CTkFrame(self.tabs["printers"], fg_color="transparent")
        self.p_edit_view = ctk.CTkScrollableFrame(self.tabs["printers"], fg_color="transparent")

    def render_printer_list(self):
        t = self.translations[self.lang]; self.p_edit_view.pack_forget(); self.p_list_view.pack(fill="both", expand=True)
        [w.destroy() for w in self.p_list_view.winfo_children()]
        ctk.CTkButton(self.p_list_view, text=t["btn_add_p"], command=self.add_printer, fg_color="#7aa2f7", text_color="black").pack(pady=20)
        scroll = ctk.CTkScrollableFrame(self.p_list_view, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        for p in self.db["printers"]:
            f = ctk.CTkFrame(scroll, fg_color="#1a1b26", corner_radius=10); f.pack(fill="x", pady=5, padx=10)
            ctk.CTkLabel(f, text=f"{p['name']} ({p.get('used_hours',0):.1f}h)", font=("Arial", 14, "bold")).pack(side="left", padx=15, pady=15)
            ctk.CTkButton(f, text=t["config"], width=80, command=lambda x=p: self.open_p_edit(x), fg_color="#24283b").pack(side="right", padx=15)

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
        self.ni_n = ctk.CTkEntry(add_f, placeholder_text=t["part_name"], width=150); self.ni_n.grid(row=0, column=0, padx=10, pady=20)
        self.ni_c = ctk.CTkEntry(add_f, placeholder_text=t["part_cost"], width=80); self.ni_c.grid(row=0, column=1, padx=5)
        self.ni_l = ctk.CTkEntry(add_f, placeholder_text=t["part_life"], width=80); self.ni_l.grid(row=0, column=2, padx=5)
        ctk.CTkButton(add_f, text="+", width=40, command=self.add_comp, fg_color="#7aa2f7", text_color="black").grid(row=0, column=3, padx=10)
        for i, c in enumerate(p.get("components", [])):
            cf = ctk.CTkFrame(self.p_edit_view, fg_color="#24283b", corner_radius=8); cf.pack(fill="x", pady=2, padx=20)
            ctk.CTkLabel(cf, text=f"{c['name']} (€{c['cost']}) - {c['used_hours']:.1f}/{c['life']}h").pack(side="left", padx=15, pady=10)
            ctk.CTkButton(cf, text="X", width=30, fg_color="red", command=lambda idx=i: self.del_comp(idx)).pack(side="right", padx=15)

    def add_comp(self):
        try:
            n, c, l = self.ni_n.get(), float(self.ni_c.get().replace(',','.')), float(self.ni_l.get().replace(',','.'))
            if n:
                if "components" not in self.current_editing_obj: self.current_editing_obj["components"] = []
                self.current_editing_obj["components"].append({"name":n, "cost":c, "life":l, "used_hours":0})
                self.save_db(); self.refresh_p_edit()
        except: pass

    def save_p(self):
        self.current_editing_obj.update({"name":self.en_p_n.get(),"base_cost":float(self.en_p_c.get()),"life":float(self.en_p_l.get()),"watt":float(self.en_p_w.get())})
        self.save_db(); self.render_printer_list()

    def del_comp(self, i): self.current_editing_obj["components"].pop(i); self.save_db(); self.refresh_p_edit()
    def add_printer(self): self.db["printers"].append({"name":"Nuova","base_cost":300,"life":5000,"used_hours":0,"watt":150,"components":[]}); self.save_db(); self.render_printer_list()
    def del_p(self): self.db["printers"].remove(self.current_editing_obj); self.save_db(); self.render_printer_list()

    # --- TAB FILAMENTI ---
    def setup_filament_tab(self):
        self.tabs["filaments"] = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.f_list_view = ctk.CTkFrame(self.tabs["filaments"], fg_color="transparent")
        self.f_edit_view = ctk.CTkScrollableFrame(self.tabs["filaments"], fg_color="transparent")

    def render_filament_list(self):
        t = self.translations[self.lang]; self.f_edit_view.pack_forget(); self.f_list_view.pack(fill="both", expand=True)
        [w.destroy() for w in self.f_list_view.winfo_children()]
        ctk.CTkButton(self.f_list_view, text=t["btn_add_f"], command=self.add_fil, fg_color="#7aa2f7", text_color="black").pack(pady=20)
        scroll = ctk.CTkScrollableFrame(self.f_list_view, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        for f in self.db["filaments"]:
            fr = ctk.CTkFrame(scroll, fg_color="#1a1b26", corner_radius=10); fr.pack(fill="x", pady=5, padx=10)
            ctk.CTkFrame(fr, width=20, height=20, corner_radius=10, fg_color=f.get("hex","#fff")).pack(side="left", padx=15)
            ctk.CTkLabel(fr, text=f"{f['brand']} {f['material']}", font=("Arial", 14, "bold")).pack(side="left", pady=15)
            ctk.CTkButton(fr, text=t["config"], width=80, command=lambda x=f: self.open_f_edit(x), fg_color="#24283b").pack(side="right", padx=15)

    def open_f_edit(self, f):
        self.current_editing_obj = f; self.f_list_view.pack_forget(); self.f_edit_view.pack(fill="both", expand=True); self.refresh_f_edit()

    def refresh_f_edit(self):
        [w.destroy() for w in self.f_edit_view.winfo_children()]
        f, t = self.current_editing_obj, self.translations[self.lang]
        ctk.CTkButton(self.f_edit_view, text=t["back"], command=self.render_filament_list, width=100).pack(pady=10)
        self.ef_b = self.create_ui_field(self.f_edit_view, "Marca", f["brand"])
        self.ef_m = self.create_ui_field(self.f_edit_view, "Materiale", f["material"])
        self.ef_c = self.create_ui_field(self.f_edit_view, "Colore", f.get("color",""))
        self.ef_h = self.create_ui_field(self.f_edit_view, "Hex Color", f.get("hex","#ffffff"))
        self.ef_p = self.create_ui_field(self.f_edit_view, "Prezzo €", f["price"])
        self.ef_w = self.create_ui_field(self.f_edit_view, "Peso g", f["weight"])
        self.ef_r = self.create_ui_field(self.f_edit_view, "Stock g", f["rem_weight"])
        ctk.CTkButton(self.f_edit_view, text=t["save"], fg_color="#9ece6a", text_color="black", command=self.save_f).pack(pady=10)
        ctk.CTkButton(self.f_edit_view, text=t["delete"], fg_color="red", command=self.del_f).pack()

    def save_f(self):
        self.current_editing_obj.update({"brand":self.ef_b.get(),"material":self.ef_m.get(),"color":self.ef_c.get(),"hex":self.ef_h.get(),"price":float(self.ef_p.get().replace(',','.')),"weight":float(self.ef_w.get().replace(',','.')),"rem_weight":float(self.ef_r.get().replace(',','.'))})
        self.save_db(); self.render_filament_list()

    def add_fil(self): self.db["filaments"].append({"brand":"Nuovo","material":"PLA","price":25,"weight":1000,"rem_weight":1000,"hex":"#ffffff"}); self.save_db(); self.render_filament_list()
    def del_f(self): self.db["filaments"].remove(self.current_editing_obj); self.save_db(); self.render_filament_list()

    def create_ui_field(self, master, label, default):
        f = ctk.CTkFrame(master, fg_color="transparent"); f.pack(fill="x", pady=4, padx=20)
        ctk.CTkLabel(f, text=label, width=150, anchor="w", font=("Arial", 14)).pack(side="left")
        e = ctk.CTkEntry(f, width=200); e.insert(0, str(default)); e.pack(side="right"); return e

    def generate_report(self):
        if not self.last_calc_data: return
        import os
        
        try:
            # Recupero oggetti dal DB per i dettagli
            p = next(x for x in self.db["printers"] if x["name"] == self.opt_p.get())
            f = next(x for x in self.db["filaments"] if f"{x['brand']} {x['material']} ({x.get('color','')})" == self.opt_f.get())
            
            # Parsing dati UI
            g = float(self.ent_g.get().replace(',','.'))
            h = float(self.ent_h.get().replace(',','.'))
            mod = float(self.ent_mod.get().replace(',','.'))
            post = float(self.ent_post.get().replace(',','.'))
            rate = float(self.ent_rate.get().replace(',','.'))
            markup = float(self.ent_markup.get().replace(',','.'))
            iva = float(self.ent_iva.get().replace(',','.'))
            e_rate = float(self.ent_elec.get().replace(',','.'))

            # Ricalcolo dettagliato per il report
            c_mat = (f['price'] / f['weight']) * g
            c_en = (p['watt'] / 1000) * h * e_rate
            c_wear_body = (p['base_cost'] / p['life']) * h
            c_wear_parts = sum((cp['cost'] / cp['life']) * h for cp in p.get('components', []))
            c_wear_total = c_wear_body + c_wear_parts
            
            tech_total = c_mat + c_en + c_wear_total
            labor_total = (mod + post) * rate
            
            valore_rincaro = (tech_total + labor_total) * (markup / 100)
            totale_pre_iva = tech_total + labor_total + valore_rincaro
            valore_iva = totale_pre_iva * (iva / 100)
            
            now = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            # Formattazione Report
            report = f"""
==================================================
           3DPRINTCALC - REPORT PREVENTIVO
==================================================
DATA: {now}
--------------------------------------------------
DETTAGLI CONFIGURAZIONE:
Stampante:     {p['name']}
Materiale:     {f['brand']} {f['material']}
Colore:        {f.get('color', 'N/D')}
--------------------------------------------------
PARAMETRI DI PRODUZIONE:
Peso Stimato:           {g} g
Tempo Stampa:           {h} h
Modellazione:           {mod} h
Post-Produzione:        {post} h
--------------------------------------------------
ANALISI COSTI TECNICI (VIVI):
Costo Filamento:        € {c_mat:.2f}
Costo Energia:          € {c_en:.2f}
Costo Usura/Manut.:     € {c_wear_total:.2f}
--------------------------------------------------
TOTALE TECNICO:         € {tech_total:.2f}
--------------------------------------------------
SERVIZI E MARGINI:
Manodopera Totale:      € {labor_total:.2f} ({mod+post}h x {rate}€/h)
Rincaro ({markup}%):         € {valore_rincaro:.2f}
IVA ({iva}%):              € {valore_iva:.2f}
--------------------------------------------------
PREZZO FINALE CLIENTE:
€ {self.last_calc_data['tot']:.2f}
--------------------------------------------------
        Grazie per aver usato 3DPrintCalc
==================================================
"""
            # Salvataggio e apertura file
            filename = f"Preventivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(report)
            
            os.startfile(filename)
            
        except Exception as e:
            print(f"Errore generazione report: {e}")

if __name__ == "__main__":
    App().mainloop()