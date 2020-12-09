import pandas as pd
from sklearn.cluster import Birch

class MicroRCA:

    def __init__(self,  
        smoothing_window=12, 
        min_periods=1, 
        branching_factor=50, 
        ad_threshold=0.045, 
        weights_alpha=0.55, 
        page_rank_alpha=0.85, 
        page_rank_max_iter=10000,
        debug=False
    ):   
        # mean and std deviation of training duration
        self.smoothing_window = smoothing_window
        self.min_periods = min_periods

        self.branching_factor = branching_factor 
        self.ad_threshold = ad_threshold
        
        self.weights_alpha = weights_alpha

        self.page_rank_alpha = page_rank_alpha
        self.page_rank_max_iter = page_rank_max_iter

        self.debug = debug


    def detect(self, traces, kpis):
        # Parse the traces and kpis
        parsed_traces = self.parse_traces(traces)
        
        # FIXME possible case where system doesn't answer for a long time and wasn't called

        #check for anomaly
        # 1 - find outlier in elapsed
        #   1.1 microRCA

        # TODO Detect anomaly
        # For each trace
        # Clustering works by grouping hosts/services. Consider (host, service) pairs ?
        # We need to have a time window of normal operation before the anomaly occured.
        # Return bad traces

        # TODO Build attribute graph
        # Hosts + Service
        # Each service connects to all the services it communicates with and all hosts it connects to (no need to differentiate!)

        # TODO Extract Subgraph
        # Find anomalous nodes (high elapsed time)
        #           We can use clustering for that
        # Extract anomalous nodes 
        # Create subgraph with anomalous nodes
        # Add nodes that are connected to these anomalous nodes
        
        # TODO Faulty service localization
        # Update weights of anomalous graph
        #           Use cases from the paper
        # Get personalization vector (Transition Probability Matrix)
        # Reverse the service-service edges
        # Apply pagerank

        # TODO Return the possible anomaly list
        return None


    def parse_traces(self, traces):
        traces = dict(tuple(traces.sort_values('traceId').groupby('traceId')))
        # for key in traces:
        #     df = traces[key].sort_values('startTime')
        #     print(df['elapsedTime'].iloc[0], df['traceId'].iloc[0], sep='\t')
        i = 1
    def parse_kpis(self, kpis):
        pass

    def anomalus_subgraph(self, DirectedGraph, anomalies, ):
        pass


if __name__ == '__main__':
    # simulate usage from the upper model
    # receives KPI and Trace information as a dataframe in the given window interval

    # load trace data
    # load kpi

    traces = pd.read_csv('data/small_trace.csv').drop(['Unnamed: 0'], axis=1)
    kpis = pd.read_csv('data/small_kpis.csv').drop(['Unnamed: 0'], axis=1)

    print(traces)

    microRCA = MicroRCA()

    res = microRCA.detect(traces, kpis)

    print(f'Result {res}')