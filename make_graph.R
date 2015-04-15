library(ggplot2)

args <- commandArgs(TRUE)
scenario <- args[1]
pattern <- args[2]
operation_mode_time_delim <- args[3]

convertMSInMinute <- function(time) {
   return (time/1000/60)
}

convertBytesInMegabytes <- function(n) {
   return (n/1024/1024)
}

name = paste(c(scenario, "-", pattern), collapse='')


data_filename = paste(c("results/", name, "-ops.data"), collapse='')
img_filename = paste(c("results/", name, "-ops.png"), collapse='')
data = read.table(data_filename, col.names=c("type", "metric", "value", "time"))
png(img_filename, height=800, width=1200)
print(qplot(
            convertMSInMinute(time),
            value, data = data, geom = "line",
            color = type,
            main=paste(scenario, '-', pattern, '- Op/s'),
            xlab="Elapsed time (minute)",
            ylab="ops"
      ) + scale_colour_discrete(name = "Compaction Strategy")
)
dev.off()

data_filename = paste(c("results/", name, "-clientrequest-write.data"), collapse='')
img_filename = paste(c("results/", name, "-clientrequest-write.png"), collapse='')
data = read.table(data_filename, col.names=c("type", "metric", "value", "time"))
png(img_filename, height=800, width=1200)
print(qplot(
            convertMSInMinute(time),
            value, data = data, geom = "line",
            color = type,
            main=paste(scenario, '-', pattern, '- ClientRequest Write Latency'),
            xlab="Elapsed time (minute)",
            ylab="Latency (ms)"
      ) + scale_colour_discrete(name = "Compaction Strategy")
)
dev.off()

data_filename = paste(c("results/", name, "-clientrequest-read.data"), collapse='')
img_filename = paste(c("results/", name, "-clientrequest-read.png"), collapse='')
data = read.table(data_filename, col.names=c("type", "metric", "value", "time"))
png(img_filename, height=800, width=1200)
print(qplot(
            convertMSInMinute(time),
            value, data = data, geom = "line",
            color = type,
            main=paste(scenario, '-', pattern, '- ClientRequest Read Latency'),
            xlab="Elapsed time (minute)",
            ylab="Latency (ms)"
      ) + scale_colour_discrete(name = "Compaction Strategy")
)
dev.off()

data_filename = paste(c("results/", name, "-compaction-bytescompacted.data"), collapse='')
img_filename = paste(c("results/", name, "-compaction-bytescompacted.png"), collapse='')
data = read.table(data_filename, col.names=c("type", "metric", "value", "time"))
png(img_filename, height=800, width=1200)
print(qplot(
            convertMSInMinute(time),
            convertBytesInMegabytes(value), data = data, geom = "line",
            color = type,
            main=paste(scenario, '-', pattern, '- MegaBytes Compacted'),
            xlab="Elapsed time (minute)",
            ylab="MegaBytes"
      ) + scale_colour_discrete(name = "Compaction Strategy")
)
dev.off()

data_filename = paste(c("results/", name, "-compaction-totalcompactionscompleted.data"), collapse='')
img_filename = paste(c("results/", name, "-compaction-totalcompactionscompleted.png"), collapse='')
data = read.table(data_filename, col.names=c("type", "metric", "value", "time"))
png(img_filename, height=800, width=1200)
print(qplot(
            convertMSInMinute(time),
            value, data = data, geom = "line",
            color = type,
            main=paste(scenario, '-', pattern, '- Total Compactions'),
            xlab="Elapsed time (minute)",
            ylab="Number of Compactions"
      ) + scale_colour_discrete(name = "Compaction Strategy")
)
dev.off()
