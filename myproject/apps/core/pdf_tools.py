import reportlab
from pathlib import Path

import io
import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm, mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import red, yellow, green

from myproject.apps.core.models import Region, Station, ConfigMAA, EnvoiMAA
from profiles.models import Profile

class MaaPDF(object):
    jours = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam']
    
    def dico(self, cle):
        dico_EN = {
            'à': 'at',
            'Origne': "Origin",
            'Aérodrome': "Airport",
            'Numéro': "Number",
            'Emis le': "Sended",
            'Validité du' : "From",
            'Jusqu\'au' : "To",
            'Message original': "Original message",
        }
        if self.langue == 'en' and cle in dico_EN.keys():
            return dico_EN[cle]
        return cle


    def set_header(self, text, can):
        """ Affiche le titre en blanc sur le carré bleu"""
        text_width = can.stringWidth(text)
        y = self.convYR(160)
        pdf_text_object = can.beginText(( self.convX(627+110)- text_width) / 2.0 , y)
        pdf_text_object.setFont("Helvetica", 14)
        pdf_text_object.setFillColorRGB(1,1,1)
        #pdf_text_object.setTextOrigin(0,y)
        pdf_text_object.textOut(text) # or: pdf_text_object.textLine(text) etc.
        can.drawText (pdf_text_object)
        
        return can

    def add_info(self, textobject, entete, value, size, color):
        """ Ajoute une info à la suite des autres"""
        #textobject.setFillColorRGB(color[0], color[1], color[2])
        textobject.setFillColorRGB(*color)
        textobject.setFont("Helvetica", size)
        
        textobject.textLine(entete + value)
        return textobject

    def get_day(self, value):
        if self.langue == 'fr':
            jour = MaaPDF.jours[int(datetime.datetime.strftime(value, "%w"))]
        else:
            jour = datetime.datetime.strftime(value, "%a")
        
        return jour

    def date_formater(self, value):
        jour = self.get_day(value)
        return datetime.datetime.strftime(value, "{} %d".format(jour))

    def datetime_formater(self, value):
        jour = self.date_formater(value)
        return datetime.datetime.strftime(value, "{} {} %H:%M UTC".format(jour, self.dico('à')))
        
    def __init__(self, fichier, envoi) -> None:
        super().__init__()

        self.langue = 'fr'
        
        buffer = io.BytesIO()

        # Create the PDF object, using the buffer as its "file."±
        p = canvas.Canvas(fichier, pagesize=A4)
        self.width, self.height = A4
        self.color_text = (0,0,0)
        self.color_red = (0.95,0,0)
        self.color_blue = (0.122,0.333,0.584)
        self.color_white = (1,1,1)
        
        self.envoi = envoi 

        p = self.set_template(p)

        #p = self.set_header("Message Avertissement Aérodrome", p)

        textobject = p.beginText(self.convX(70), self.convYR(200))
        
        textobject = self.add_info(textobject, self.dico("Message Avertissement Aérodrome"), "", 20, self.color_text)
        textobject = self.add_info(textobject, "", "", 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Origine")+"        : ", "Météo-France", 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Aérodrome")+"  : ", envoi.configmaa.station.oaci, 16, self.color_text)
        textobject = self.add_info(textobject, "", "", 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Numéro")+"       : ", str(envoi.numero), 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Emis le")+"        : ", self.datetime_formater(envoi.date_envoi), 16, self.color_text)
        textobject = self.add_info(textobject, "", "", 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Validité du")+"   : ", self.datetime_formater(envoi.date_debut), 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Jusqu'au")+"      : ", self.datetime_formater(envoi.date_fin), 16, self.color_text)
        textobject = self.add_info(textobject, "", "", 16, self.color_text)
        textobject = self.add_info(textobject, "Rafale ou Vent max prévu >= à 40 KT.", "", 20, self.color_red)
        textobject = self.add_info(textobject, "", "", 16, self.color_text)
        textobject = self.add_info(textobject, self.dico("Message original")+" : ", "", 16, self.color_text)
        messages = envoi.message.split("\n")
        for mess in messages:
            textobject = self.add_info(textobject, mess, "", 14, self.color_text)
        
        p.drawText(textobject)

        p = self.insert_wind_table(p, self.envoi)

        # Close the PDF object cleanly, and we're done.
        p.showPage()
        
        p.save()

    def insert_wind_table_frame(self, can, N, X, Y, W, H, dtbase, unite):
        """ Insère le tableau des valeurs de vent entre 55x627
            X, Y sont les coordonnées du haut gauche du tableau
            N est le nobmre de colonne
            W la largeur du tableau
            H la hauteur du tableau
        """
        largeur_case = W / N
        hauteur_utile = self.convY(H*0.80)
        milieu_caseY = Y + hauteur_utile*0.75

        can.setFont("Helvetica", 10)
        can.setStrokeColorRGB(*self.color_blue)
        can.setFillColorRGB(1,1,1)

        # Cadre général
        can.rect(X, Y, W, H,  fill=1)

        # Cadres intermédiaires
        for i in range(0,N):
            Xi = X + (i*largeur_case)
            can.rect(Xi, Y, largeur_case, hauteur_utile,  fill=1)
        
        # Jour
        can.setFillColorRGB(0.122,0.333,0.584)
        can.drawString(X+1, Y+H-12, self.date_formater(dtbase))

        # Heures
        for i in range(0, N):
            Xi = X + (i*largeur_case)
            new_date = dtbase+ datetime.timedelta(hours=i)
            heure = new_date.strftime("%HTU")
            can.drawString(Xi+2, Y+hauteur_utile+3, heure)
            if heure == '00TU':
                can.drawString(Xi+1, Y+H-12, self.date_formater(new_date))
                can.line(Xi, Y+hauteur_utile, Xi, Y+H)

        # Insère picto vent
        for i in range(0, N):
            Xi = X + (i*largeur_case)
            milieu_caseX = Xi+largeur_case/2
            new_date = dtbase+ datetime.timedelta(hours=i)

            if i==3:
                can = self.draw_variable(can, milieu_caseX, milieu_caseY, largeur_case, hauteur_utile*0.25)
            else:
                can = self.draw_triangle(can, milieu_caseX, milieu_caseY, largeur_case, hauteur_utile*0.25, i*30)
            

        # Insère données vent
        can.setFillColor(self.color_blue)
        can.setFont("Helvetica", 8)
        for i in range(0, N):
            can.setFillColor(self.color_blue)
            Xi = X + (i*largeur_case)
            if i==3:
                can.drawString(Xi+3, Y+hauteur_utile*0.35, "VRB")
            else:
                can.drawString(Xi+3, Y+hauteur_utile*0.35, str(i*30)+"°")
            can.drawString(Xi+3, Y+hauteur_utile*0.2, "120"+unite)
            can.setFillColor(self.color_red)
            can.drawString(Xi+3, Y+hauteur_utile*0.05, "150"+unite)
            
        
        return can

    def draw_variable(self, can, milieuX, milieuY, ldispo, hdispo):
        can.setFillColor(self.color_red)
        rayon = min(ldispo, hdispo)*0.5
        can.circle(milieuX, milieuY, rayon, stroke=1, fill=1)
        can.setFillColor(self.color_white)
        rayon = min(ldispo, hdispo)*0.2
        can.circle(milieuX, milieuY, rayon, stroke=1, fill=1)
        return can

    def draw_triangle(self, can, X, Y, ldispo, hdispo, direction):
        """ Dessine un triangle décrivant la direction du vent 
            X et Y coordonées du centre du traingle
            taille : hauteur entre le sommet et le centre
        """
        taille = min(ldispo, hdispo)*1.3
        can.translate(X,Y)
        can.rotate(-direction)
        p = can.beginPath()
        p.moveTo(-taille*0.4, -taille*0.5)
        p.lineTo(-taille*0.1, taille*0.6)
        p.lineTo(taille*0.1, taille*0.6)
        p.lineTo(taille*0.4, -taille*0.5)
        p.lineTo(-taille*0.4, -taille*0.5)
        can.setFillColor(self.color_red)
        can.setStrokeColor(self.color_white)
        can.drawPath(p, fill=1)

        can.setFillColor(self.color_white)
        can.setStrokeColor(self.color_white)
        can.rect(-taille*0.5, -taille*0.3, taille, taille*0.1, fill=1)
        can.rect(-taille*0.5, 0, taille, taille*0.1, fill=1)
        can.rect(-taille*0.5, taille*0.3, taille, taille*0.1, fill=1)

        can.rotate(direction)
        can.translate(-X,-Y)

        return can

    def insert_wind_table(self, can, envoi):
        """ Insère le tableau des valeurs de vent  55x627  l:24 par colonne 
        """
        unite = envoi.configmaa.station.wind_unit
        N = 12
        dtbase = envoi.date_envoi
        if dtbase.minute != 0 :
            dtbase = dtbase.replace(minute=0)
        dtbase = dtbase + datetime.timedelta(hours=1)

        can = self.insert_wind_table_frame(can, N, self.convX(56), self.convYR(750), self.convX(625), self.convY(120), dtbase, unite)

        dtbase = dtbase + datetime.timedelta(hours=N)
        can = self.insert_wind_table_frame(can, N, self.convX(56), self.convYR(911), self.convX(625), self.convY(120), dtbase, unite)


        return can

    def convY(self, value):
        return value * self.height / 1000

    def convYR(self, value):
        return self.height - (value * self.height / 1000)

    def convX(self, value):
        return value * self.width / 707

    def set_template(self, can):
        width, height = A4

        # Définit le font gradient
        #-------------------------------------------------------------------------------
        can.linearGradient(0, height/2, width, height/2, ((0.933,0.941,0.875), (1,1,1)))
        can.line(105*mm, 200*mm, 180*mm, 100*mm)
        
        # Insert logo MF
        #-------------------------------------------------------------------------------
        rep = Path(__file__).parent
        logo = rep.joinpath("media").joinpath('logo_mf.png')
        w = self.convY(100)
        can.drawInlineImage(str(logo.absolute()), self.convX(55), self.convYR(120), w, w)

        # Titre MAA
        text = "[ MAA ]"
        y = self.convYR(80)
        pdf_text_object = can.beginText()
        pdf_text_object.setTextOrigin(self.convX(317),y)
        pdf_text_object.setFont("Helvetica", 30)
        pdf_text_object.setFillColorRGB(0.122,0.333,0.584)
        pdf_text_object.textOut(text)
        can.drawText (pdf_text_object)

        # Définit le cadre 
        can.setStrokeColorRGB(0.122,0.333,0.584)
        can.setFillColorRGB(1,1,1)
        can.rect(self.convX(55), self.convYR(911), self.convX(627), self.convY(761),  fill=1)

        # Dessine le bloque avertissement
        can.setFillColorRGB(0.122,0.333,0.584)
        can.rect(self.convX(55), self.convYR(168), self.convX(627), self.convY(28),  fill=1)

        return can


    
    