

data2019 <- data.frame("Outbreak" = NA,
                       "Date" = NA,
                       "Year" = NA,
                       "Month" = NA,
                       "Day" = NA,
                       "Description" = NA,
                       "Link" = NA)

for(page in 1:6){
  
  webpage <- read_html(paste0("https://reliefweb.int/updates?advanced-search=%28S1275%29_%28DO20190101-20191231%29&search=%22disease%20outbreak%20news%22&page=", page-1))
  
  # Extracting the title of the DON from each DON
  newsoutbreaks <- webpage %>% 
    html_nodes("article") %>%
    html_node("h4") %>%
    html_text2()
  
  # Extracting the link from each DON
  newslink <- webpage %>% 
    html_nodes("article") %>%
    html_node("header") %>%
    html_node("h4") %>%
    html_node("a") %>%
    html_attr("href")
  
  for(news in 1:length(newsoutbreaks)){
    data2019[(page-1)*20+news, "Link"] <- newslink[news]
    data2019[(page-1)*20+news, "Outbreak"] <- newsoutbreaks[news]
    
    # Extracting the information on date from each DON
    data2019[(page-1)*20+news, "Date"] <- read_html(newslink[news]) %>%
      html_node("dl.meta.core") %>%
      html_element("dd.date.published") %>%
      html_text2()  
    
    # Extracting the Description from each DON
    data2019[(page-1)*20+news, "Description"] <- read_html(newslink[news]) %>%
      html_nodes("div.content") %>%
      html_nodes("div.content") %>%
      html_text2()
  }
} # 119 DON´s related to 2019

data2019 <- data2019 %>% 
  mutate(Date = as.Date(Date, format = "%d %b %Y")) %>% 
  mutate(Year = get_year(Date), 
         Month = get_month(Date), 
         Day = get_day(Date))
