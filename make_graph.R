library(ggplot2)

args <- commandArgs(TRUE)
operation_mode_time_delim <- args[1]

convertMSInMinute <- function(time) {
   return (time/1000/60)
}

convertBytesInMegabytes <- function(n) {
   return (n/1024/1024)
}

data = read.table("results/sizetieredcompactionstrategy-write-clientrequest-write.data", col.names=c("type", "value", "time"))
png("results/sizetieredcompactionstrategy-write-clientrequest-write-95th.png")
print(qplot(
            convertMSInMinute(time - min(time)),
            value, data = data, geom = "line",
            color = type,
            main='ClientRequest Write Latency',
            xlab="Elapsed time (minute)",
            ylab="Latency (ms)"
      ) + scale_colour_discrete(name = "Operation Mode", labels=c("Pattern1", "Pattern2"))
)
dev.off()

data = read.table("results/sizetieredcompactionstrategy-write-clientrequest-read.data", col.names=c("type", "value", "time"))
png("results/sizetieredcompactionstrategy-write-clientrequest-read-95th.png")
print(qplot(
            convertMSInMinute(time - min(time)),
            value, data = data, geom = "line",
            color = type,
            main='ClientRequest Read Latency',
            xlab="Elapsed time (minute)",
            ylab="Latency (ms)"
      ) + scale_colour_discrete(name = "Operation Mode", labels=c("Pattern1", "Pattern2"))
)
dev.off()

data = read.table("results/sizetieredcompactionstrategy-write-compaction-bytescompacted.data", col.names=c("type", "value", "time"))
png("results/sizetieredcompactionstrategy-write-compaction-bytescompacted.png")
print(qplot(
            convertMSInMinute(time - min(time)),
            convertBytesInMegabytes(value), data = data, geom = "line",
            color = type,
            main='MegaBytes Compacted',
            xlab="Elapsed time (minute)",
            ylab="MegaBytes"
      ) + scale_colour_discrete(name = "Operation Mode", labels=c("Pattern1", "Pattern2"))
)
dev.off()

data = read.table("results/sizetieredcompactionstrategy-write-compaction-totalcompactionscompleted.data", col.names=c("type", "value", "time"))
png("results/sizetieredcompactionstrategy-write-compaction-totalcompactionscompleted.png")
print(qplot(
            convertMSInMinute(time - min(time)),
            value, data = data, geom = "line",
            color = type,
            main='Total Compactions',
            xlab="Elapsed time (minute)",
            ylab="Number of Compactions"
      ) + scale_colour_discrete(name = "Operation Mode", labels=c("Pattern1", "Pattern2"))
)
dev.off()
