import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup

url_site = 'https://books.toscrape.com/'
base_currency = 'gbp'
end_currency = 'eur'

url_change = f'https://api.frankfurter.dev/v2/rate/{base_currency}/{end_currency}'

def extract() :


    #extract sales
    sales = pd.read_csv('sales_raw.csv')
    sales['order_date'] = pd.to_datetime(sales['order_date'])



    #extract category_rules, channels, countries
    connexion = sqlite3.connect('bookworld_reference.db')

    #Faire le dictionnaire queries puis le transformer en .sql
    queries = {
        'category_rules' : 'SELECT * FROM category_rules',
        'channels' : 'SELECT * FROM channels',
        'countries' : 'SELECT * FROM countries',
        'category_rules_filtered' : 'SELECT * FROM category_rules WHERE is_active ',
    }

    #Créer le doc queries et fait une boucle pour ajouter chacune des query
    with open("queries.sql","w") as fichier :
      for query in queries.values():
        fichier.write(f"{query}; \n")


    category_rules = pd.read_sql(queries['category_rules'],connexion)

    channels = pd.read_sql(queries['channels'], connexion)

    countries = pd.read_sql(queries['countries'],connexion)



    #Webscrapper livres
    #Initialiser dans le cas où la request ne fonctionne pas
    livres = None
    #Timeout au cas où l'url n'existe plus
    try :
        page = requests.get(url_site, timeout=10)
        page.raise_for_status()
        soup = BeautifulSoup(page.content)

        livre_main = soup.find_all("li", class_ = "col-xs-6 col-sm-4 col-md-3 col-lg-3")

        livre_titres =[]
        livre_prix = []

        for i in livre_main :
            livre_titres.append(i.find("a", href = True, title = True)["title"])

        for i in livre_main:
            livre_prix.append(i.find("p", {"class" : "price_color"}).get_text().strip())

        livres_int = {
            "titre" : livre_titres,
            "prix" : livre_prix
        }
        livres = pd.DataFrame(livres_int)

    except requests.exceptions.RequestException as erreur:
        print("Erreur lors de la requête :", erreur)

    if livres is None :
      raise ValueError('Pas de livre récupérés')

    #Utiliser l'API Frankfurter
    #Initialiser dans le cas où la request ne fonctionne pas
    taux = None
    #Timeout au cas où l'url n'existe plus
    try :
        change = requests.get(url_change, timeout=10)
        change.raise_for_status()
        change_json = change.json()
        taux = change_json['rate']

    except requests.exceptions.RequestException as erreur:
        print("Erreur lors de la requête :", erreur)

    if taux is None :
      raise ValueError('Pas de taux récupérés')


    return sales, category_rules, channels, countries, livres, taux

def transform() :
  sales, category_rules, channels, countries, livres, taux= extract()

  livres = livres.rename(columns={
    'titre':'book_name',
    'prix':'price'
})

  #créer un df intermédiaire où on prend que les colonnes souhaitées
  sales_enriched = sales[['country_code','quantity','discount_rate','book_name','order_id']].merge(countries[['country_code','country_name']],on='country_code',how='left')

  sales_enriched = sales_enriched.merge(livres,on='book_name',how='left')

  #Nettoyer la colonne price pour pouvoir l'utiliser en float
  sales_enriched['price'] = sales_enriched['price'].str.replace('£','')
  sales_enriched['price'] = pd.to_numeric(sales_enriched['price'])

  #Vérifier si il y a des livres qui n'ont pas de correspondance
  check = sales_enriched['price'].isna().sum()
  if check > 0 :
    print (f"Il y a {check} livres qui n'ont pas de prix")


  #Créer les colonnes revenue_by_sale_gbp et revenue_by_sale_eur
  sales_enriched['revenue_by_sale_gbp'] = sales_enriched['quantity'] * (sales_enriched['price']*(1 - sales_enriched['discount_rate']))
  sales_enriched['revenue_by_sale_eur'] = sales_enriched['revenue_by_sale_gbp'] * taux


  #Le groupby final
  sales_by_country = sales_enriched.groupby(['country_code','country_name']).agg(
    total_orders = ('order_id', 'count'),
    total_quantity = ('quantity','sum'),
    total_revenu_gbp = ('revenue_by_sale_gbp','sum'),
    total_revenu_eur = ('revenue_by_sale_eur','sum')
  ).reset_index()

  #Modifications pour la RGPD avec création d'un customer_id pour les clients pour qu'on puisse faire une étupde par client si nécessaire
  #DropDuplicate pour avoir qu'une seule ligne par combinaison
  clients = sales[['customer_first_name', 'customer_last_name']].drop_duplicates().reset_index(drop=True)

  clients['customer_id'] = range(1, len(clients) + 1)

  sales = sales.merge(clients,on=['customer_first_name', 'customer_last_name'],how='left')
  sales = sales.drop(columns=['customer_first_name', 'customer_last_name'])

  return sales_by_country, sales, category_rules, channels, countries, livres, taux

def load() :
  sales_by_country, sales, category_rules, channels, countries, livres, taux= transform()

  schema_final = """
  CREATE TABLE IF NOT EXISTS sales_by_country (
      country_code TEXT,
      country_name TEXT,
      total_orders INTEGER,
      total_quantity INTEGER,
      total_revenu_gbp REAL,
      total_revenu_eur REAL
  );

  CREATE TABLE IF NOT EXISTS sales (
      order_id TEXT,
      order_date TEXT,
      book_id TEXT,
      country_code TEXT,
      channel_code TEXT,
      quantity INTEGER,
      discount_rate REAL,
      book_name TEXT,
      customer_id INT
  );

  CREATE TABLE IF NOT EXISTS category_rules (
      category_name TEXT,
      margin_rate REAL,
      strategic_flag INTEGER,
      default_channel_code TEXT,
      is_active INTEGER
  );

  CREATE TABLE IF NOT EXISTS channels (
      channel_code TEXT,
      channel_name TEXT,
      acquisition_cost_gbp REAL,
      channel_group TEXT,
      is_active INTEGER
  );

  CREATE TABLE IF NOT EXISTS countries (
      country_code TEXT,
      country_name TEXT,
      currency_code TEXT,
      vat_rate REAL,
      region TEXT,
      is_active INTEGER
  );

  CREATE TABLE IF NOT EXISTS livres (
      book_name TEXT,
      price REAL
  );
  """
#Créer le doc schema_final.sql
  with open("schema_final.sql", "w") as fichier:
    fichier.write(schema_final)
#Créer et ouvrir le doc projet_final_database.db
  connexion = sqlite3.connect('projet_final_database.db')

#Remplir les tables
  sales_by_country.to_sql("sales_by_country", connexion, if_exists="replace", index=False)
  sales.to_sql("sales", connexion, if_exists="replace", index=False)
  category_rules.to_sql("category_rules", connexion, if_exists="replace", index=False)
  channels.to_sql("channels", connexion, if_exists="replace", index=False)
  countries.to_sql("countries", connexion, if_exists="replace", index=False)
  livres.to_sql("livres", connexion, if_exists="replace", index=False)

  connexion.close()

#Juste pour lui donner un nom plus classique, on pourrait juste appeler load en soit
def run_pipeline() :
    load()

if __name__ == "__main__":
    run_pipeline()  