library(ggplot2)

args <- commandArgs(TRUE)
operation_mode_time_delim <- args[1]

convertMSInMinute <- function(time) {
   return (time/1000/60)
}

convertBytesInMegabytes <- function(n) {
   return (n/1024/1024)
}

data = read.table("results/clientrequest-write-95th.txt", col.names=c("type", "value", "time"))
png("results/clientrequest-write-95th.png")
print(qplot(
            convertMSInMinute(time - min(time)),
            value, data = data, geom = "line",
            color = time>operation_mode_time_delim,
            main='ClientRequest Write Latency during a stress session',
            xlab="Elapsed time (minute)",
            ylab="Latency (ms)"
      ) + scale_colour_discrete(name = "Operation Mode", labels=c("WRITE", "READ"))
)
dev.off()

