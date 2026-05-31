import threading
import time
import sqlite3

class Masa:
    def __init__(self, masa_id):
        self.masa_id = masa_id
        self.sure_doldumu = False
        self.durumu_dbden_cek() 
    def durumu_dbden_cek(self):
        baglanti = sqlite3.connect("kutuphane.db")
        imlec = baglanti.cursor()
        imlec.execute("SELECT durum FROM Masalar WHERE masa_id = ?", (self.masa_id,))
        sonuc = imlec.fetchone()
        if sonuc:
            self.durum = sonuc[0]
        else:
            self.durum = "boş"
        baglanti.close()
    def veritabanini_guncelle(self, yeni_durum, tc_no=None):
        baglanti = sqlite3.connect("kutuphane.db")
        imlec = baglanti.cursor()
        imlec.execute("""
            UPDATE Masalar 
            SET durum = ?, oturan_tc = ? 
            WHERE masa_id = ?
        """, (yeni_durum, tc_no, self.masa_id))
        baglanti.commit()
        baglanti.close()
        self.durum = yeni_durum
    def rezerve_et(self, aktif_tc):
        if self.durum != "boş":
            print(f"[HATA] Masa {self.masa_id} şu an uygun değil (Durum: {self.durum}).")
            return
        self.veritabanini_guncelle("rezerve", aktif_tc)
        self.sure_doldumu = False
        print(f"\nMasa {self.masa_id} rezerve edildi.")
        print("Kişinin giriş yapması bekleniyor...")
        sayac_thread = threading.Thread(target=self.arkaplan_sayaci, args=(15,), daemon=True)
        sayac_thread.start()
        while self.durum == "rezerve":
            girdi = input(f"Masa {self.masa_id} için 'giriş' yazın: ").strip().lower()
            if self.sure_doldumu:
                print(f"Geç kaldınız. Masa {self.masa_id} rezervasyonu iptal edildi.")
                break
            if girdi == "giriş":
                self.veritabanini_guncelle("dolu", aktif_tc)
                print(f"Masa {self.masa_id} onaylandı. Durum: Dolu")
                break
    def arkaplan_sayaci(self, sure):
        for kalan_sure in range(sure, 0, -1):
            if self.durum == "dolu":
                return
            time.sleep(1)
        if self.durum == "rezerve":
            self.veritabanini_guncelle("boş", None)
            self.sure_doldumu = True
            print(f"\n[SİSTEM SÜRESİ DOLDU] Masa {self.masa_id} rezervasyonu iptal edildi.")
    def masadan_tamamen_kalk(self):
        self.veritabanini_guncelle("boş", None)
        print(f"\nMasa {self.masa_id} boşaltıldı. İyi günler dileriz!")


kutuphane_masalari=[]
for i in range(1,11):
    yeni_masa=Masa(i)
    kutuphane_masalari.append(yeni_masa)

def rezervasyon_olustur(aktif_tc):
    print("\n--- Masa Rezervasyonu ---")
    bos_masalar_var_mi = False
    for masa in kutuphane_masalari:
        if masa.durum == "boş":
            print(f"Masa {masa.masa_id} rezerve edilebilir.")
            bos_masalar_var_mi = True 
    if not bos_masalar_var_mi:
        print("Şu an kütüphanede hiç boş masa yok!")
        return
    try:
        istenen_masa_id = int(input("\nHangi masaya rezervasyon oluşturmak istersiniz (İptal için 0): "))
        if istenen_masa_id == 0:
            return
        secilen_masa = None
        for masa in kutuphane_masalari:
            if masa.masa_id == istenen_masa_id:
                secilen_masa = masa
                break
        if secilen_masa:
            secilen_masa.rezerve_et(aktif_tc)
            while secilen_masa.durum == "dolu":
                print(f"\n>>> Masa {secilen_masa.masa_id}'de çalışıyorsunuz <<<")
                girdi = input("Masadan tamamen kalkmak ve çıkmak için 'kalk' yazın: ").strip().lower()
                if girdi == "kalk":
                    secilen_masa.masadan_tamamen_kalk()
                    break 
                else:
                    print("Geçersiz komut. (Mola sistemi yakında eklenecektir)")
        else:
            print("[HATA] Geçersiz masa numarası girdiniz.")        
    except ValueError:
        print("[HATA] Lütfen sadece rakam giriniz!")

def kitap_kirala(aktif_tc):
    print("\n--- Kitap Kiralama ---")
    baglanti = sqlite3.connect("kutuphane.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT kitap_id, kitap_adi FROM Kitaplar")
    kitaplar = imlec.fetchall()
    if not kitaplar:
        print("Şu an kütüphanede hiç kitap yok!")
        return
    for kitap in kitaplar:
        print(f"[{kitap[0]}] {kitap[1]}")
    try:
        secim = int(input("\nKiralamak istediğiniz kitabın ID'sini giriniz (İptal için 0): "))
        if secim == 0:
            return
        imlec.execute("SELECT kitap_adi FROM Kitaplar WHERE kitap_id=?", (secim,))
        if not imlec.fetchone():
            print("[HATA] Geçersiz kitap numarası girdiniz!")
            return
        kiralama_suresi = int(input("Kaç gün kiralamak istersiniz?: "))
        imlec.execute("""
            INSERT INTO Kiralamalar (kiralayan_tc, kiralanan_kitap_id, kiralama_gun)
            VALUES (?, ?, ?)
        """, (aktif_tc, secim, kiralama_suresi))
        baglanti.commit()
        print(f"\n[BAŞARILI] İşlem tamam! Kitap {kiralama_suresi} günlüğüne hesabınıza kiralandı.")
    except ValueError:
        print("[HATA] Lütfen harf değil, sadece rakam giriniz!")
    finally:
        baglanti.close()

def kitap_oku():
    print("\n--- Kitap Okuma (PDF/TXT Modu) ---")
    baglanti = sqlite3.connect("kutuphane.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT kitap_id, kitap_adi FROM Kitaplar")
    kitaplar = imlec.fetchall()
    for kitap in kitaplar:
        print(f"[{kitap[0]}] {kitap[1]}")
    try:
        secim = int(input("\nOkumak istediğiniz kitabın ID'sini giriniz (İptal için 0): "))
        if secim == 0:
            return   
        imlec.execute("SELECT dosya_yolu, kitap_adi FROM Kitaplar WHERE kitap_id=?", (secim,))
        sonuc = imlec.fetchone()
        if sonuc:
            dosya_yolu = sonuc[0]
            kitap_adi = sonuc[1]
            print(f"\n>>> {kitap_adi} Yükleniyor... <<<\n")
            print("-" * 40)
            with open(dosya_yolu, "r", encoding="utf-8") as dosya:
                print(dosya.read())
            print("-" * 40)
            print("\n[BİLGİ] Okuma tamamlandı.")
        else:
            print("[HATA] Girdiğiniz ID ile eşleşen bir kitap bulunamadı.")
    except ValueError:
        print("[HATA] Lütfen sadece rakam giriniz!")
    except FileNotFoundError:
        print("\n[KRİTİK HATA] Kitap veritabanında kayıtlı, ancak fiziksel metin dosyası klasörde bulunamadı!")
    finally:
        baglanti.close()

import sqlite3

def not_al(aktif_tc):
    print("\n--- Kişisel Çalışma Not Defteri ---")
    ders_adi = input("Çalışılan dersin adını giriniz: ")
    calisma_saati = input("Kaç saat çalıştınız: ")
    baglanti = sqlite3.connect("kutuphane.db")
    imlec = baglanti.cursor()
    imlec.execute("""
        INSERT INTO Notlar (tc_no, ders_adi, calisma_saati)
        VALUES (?, ?, ?)
    """, (aktif_tc, ders_adi, calisma_saati))
    baglanti.commit()
    baglanti.close()
    print("\n[BAŞARILI] Harika! Çalışma kaydınız kişisel defterinize işlendi.")
        
def notlarimi_gor(aktif_tc):
    print("\n--- Geçmiş Çalışma Kayıtlarım ---")
    
    baglanti = sqlite3.connect("kutuphane.db")
    imlec = baglanti.cursor()
    imlec.execute("SELECT ders_adi, calisma_saati FROM Notlar WHERE tc_no = ?", (aktif_tc,))
    notlar = imlec.fetchall()
    baglanti.close()
    if notlar:
        toplam_saat = 0
        for kayit in notlar:
            ders = kayit[0]
            saat = int(kayit[1])
            toplam_saat += saat
            print(f"> {ders} dersine {saat} saat çalışıldı.")
        print("-" * 30)
        print(f"Toplam Çalışma Süresi: {toplam_saat} Saat")
    else:
        print("Henüz hiç çalışma kaydınız bulunmuyor. Masa rezerve edip çalışmaya başlayabilirsiniz!")


def uyemenu(kullanici_adi, aktif_tc):
    print(f"\n--- [ {kullanici_adi.upper()} | ÜYE MENÜSÜ ] ---")
    while True:
        print("\nLütfen yapmak istediğiniz işlemi seçiniz:")
        print("(1) Rezervasyon Oluştur")
        print("(2) Kitap Kirala ")
        print("(3) Kitap Oku ")
        print("(4) Not al")
        print("(5) Notlarımı görüntüle")
        print("(6) Çıkış yap") 
        secim = input("Seçim: ").strip()
        if secim == "1":
            rezervasyon_olustur(aktif_tc)
        elif secim == "2":
            print("Kitap kiralama modülü veritabanına bağlanılıyor...")
            kitap_kirala(aktif_tc)
        elif secim == "3":
            print("Kitap okuma modülü veritabanına bağlanılıyor...")
            kitap_oku()
        elif secim == "4":
            print("Not almanız için veritabanına bağlanılıyor....")
            not_al(aktif_tc)
        elif secim == "5":
            print("Notlarınızı görüntülemek için veritabanına bağlanılıyor....")
            notlarimi_gor(aktif_tc)
        elif secim == "6":
            break
        else:
            print("[HATA] Geçersiz seçim! Lütfen tekrar deneyin.")

def admin_menu():
    print("\n--- [ YÖNETİCİ (ADMIN) MENÜSÜ ] ---")
    while True:
        print("\nLütfen yapmak istediğiniz işlemi seçiniz:")
        print("(1) Masaların Anlık Durumunu Gör")
        print("(2) Kayıtlı Üyeleri Listele")
        print("(3) Zombi Masaları Temizle (Tümünü Boşalt)")
        print("(4) Çıkış Yap")
        secim = input("Seçim: ").strip()
        if secim == "1":
            baglanti = sqlite3.connect("kutuphane.db")
            imlec = baglanti.cursor()
            imlec.execute("""
                SELECT Masalar.masa_id, Masalar.durum, Kullanicilar.kullanici_adi 
                FROM Masalar 
                LEFT JOIN Kullanicilar ON Masalar.oturan_tc = Kullanicilar.tc_no
            """)
            masalar_listesi = imlec.fetchall()
            baglanti.close()
            print("\n--- ANLIK MASA DURUMLARI ---")
            for masa in masalar_listesi:
                masa_id = masa[0]
                durum = masa[1]
                oturan_kisi = masa[2] if masa[2] else "-" 
                print(f"Masa {masa_id}: {durum.upper()} | Oturan: {oturan_kisi}")
        elif secim == "2":
            baglanti = sqlite3.connect("kutuphane.db")
            imlec = baglanti.cursor()
            imlec.execute("SELECT tc_no, kullanici_adi FROM Kullanicilar WHERE rol='üye'")
            uyeler = imlec.fetchall()
            baglanti.close()
            print("\n--- KAYITLI ÜYELER ---")
            for uye in uyeler:
                print(f"Kullanıcı: {uye[1]} | TC: {uye[0]}")
        elif secim == "3":
            onay = input("Tüm masalar zorla boşaltılacak! Emin misiniz? (e/h): ").strip().lower()
            if onay == 'e':
                baglanti = sqlite3.connect("kutuphane.db")
                imlec = baglanti.cursor()
                imlec.execute("UPDATE Masalar SET durum='boş', oturan_tc=NULL")
                baglanti.commit()
                baglanti.close()
                for m in kutuphane_masalari:
                    m.durumu_dbden_cek()
                print("[SİSTEM] Tüm masalar başarıyla sıfırlandı!")
            else:
                print("İşlem iptal edildi.")
        elif secim == "4":
            print("Admin menüsünden çıkılıyor. Ana ekrana dönülüyor...")
            break
        else:
            print("[HATA] Geçersiz seçim! Lütfen tekrar deneyin.")

def uye_ol():
    print("\n--- Kayıt Ekranı ---")
    tc_no = input("TC Numaranızı giriniz: ")
    kullanici_adi = input("Kullanıcı adınızı giriniz: ")
    sifre = input("Şifrenizi giriniz: ") 
    try:
        baglanti = sqlite3.connect("kutuphane.db")
        imlec = baglanti.cursor()
        imlec.execute("""
            INSERT INTO Kullanicilar (tc_no, kullanici_adi, sifre, rol)
            VALUES (?, ?, ?, 'üye')
        """, (tc_no, kullanici_adi, sifre))
        baglanti.commit()
        print("\n[BAŞARILI] Harika! Sisteme başarıyla kayıt oldunuz, şimdi giriş yapabilirsiniz.")
    except sqlite3.IntegrityError:
        print(f"\n[HATA] {tc_no} kimlik numarası ile zaten sistemde bir kayıt bulunuyor!")
    finally:
        baglanti.close()

def giris_yap():
    print("\n--- Giriş Ekranı ---")
    kullanici_adi = input("Kullanıcı adınızı giriniz: ")
    sifre = input("Şifrenizi giriniz: ")
    baglanti = sqlite3.connect("kutuphane.db")
    imlec = baglanti.cursor()
    imlec.execute("""
        SELECT rol, tc_no FROM Kullanicilar 
        WHERE kullanici_adi = ? AND sifre = ?
    """, (kullanici_adi, sifre))
    kullanici = imlec.fetchone() 
    baglanti.close()
    if kullanici:
        rol = kullanici[0]
        aktif_tc = kullanici[1]
        print(f"\n[BAŞARILI] Hoşgeldiniz, {kullanici_adi}!")
        if rol == 'admin':
            print("Yetkiler doğrulandı. Admin menüsü açılıyor...")
            admin_menu() 
        else:
            print("Üye menüsü açılıyor...")
            uyemenu(kullanici_adi, aktif_tc) 
    else:
        print("\n[HATA] Kullanıcı adı veya şifre hatalı! Lütfen tekrar deneyin.")

print("Kütüphane sistemine HOŞGELDİNİZ")
while True:
    print("Lütfen yapmak istediğiniz işlemi seçiniz")
    durum=input("(1)Üye Ol\n(2)Giriş Yap\n(3)Çıkış Yap\nSeçim:")
    if durum=="1":
        uye_ol()
    elif durum=="2":
        giris_yap()
    elif durum=="3":
        print("Çıkış yapılıyor..")
        break
    else:
        print("Geçersiz girdi lütfen yeniden deneyiniz")