"""
    Programme pour compléter le sel de la piscine
"""
import sys
def exit_program():
    print("Sortie du programme...")
    sys.exit(0)

print("Pour utiliser le programme, il faut avoir relevé le taux de salinité avec un testeur électronique")
reponse_test = input("Disposez-vous du taux de salinité actuel ? (Y ou N) : ")
if reponse_test =='Y' or reponse_test=='y':
    #Entrées des salinités 
    Salinite_demandee = float(input("Taux de salinité demandé pour l'électrolyseur : "))
    Salinite_relevee = float(input("Taux de salinité relevé par le testeur électronique : "))
    #Entrées des mesures
    LongueurBassin = int(input("Entrez la longeur du bassin en mètres : "))
    largeurBassin = int(input("Entrez la largeur du bassin en mètres : "))
    ProfondeurBassin = float(input("Entrez la profondeur du bassin en mètres : "))
else :
    exit_program() 
volume_du_bassin = LongueurBassin*largeurBassin*ProfondeurBassin

#print(type(volume_du_bassin))
contenance_bassin = volume_du_bassin*1000
#print("volume du bassin = ",volume_du_bassin,"m3 soit une contenance de : ",contenance_bassin," litres d'eau")
print("Il faut ajouter",int((Salinite_demandee-Salinite_relevee)*contenance_bassin/1000),"Kg de sel pour ce bassin de",volume_du_bassin,"m3")
print("cette valeur est arrondie au Kg inférieur")


