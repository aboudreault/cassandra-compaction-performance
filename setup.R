local({r <- getOption("repos"); 
       r["CRAN"] <- "http://cran.r-project.org"; options(repos=r)})
update.packages()
install.packages('ggplot2', dependencies=TRUE)
