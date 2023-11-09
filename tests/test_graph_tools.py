def test_map_reduce():
    from xradio.data.datasets import download
    from graphviper.graph_tools import map
    import dask

    import dask
    dask.config.set(scheduler="synchronous")

    ps_name = "Antennae_North.cal.lsrk.split.vis.zarr"
    download(file=ps_name, source="dropbox")

    from xradio.vis.read_processing_set import read_processing_set

    # fields = ["NGC4038 - Antennae North"]
    intents = ["OBSERVE_TARGET#ON_SOURCE"]
    fields = None
    ps = read_processing_set(
        ps_name=ps_name,
        intents=["OBSERVE_TARGET#ON_SOURCE"],
        fields=fields,
    )
    ms_xds = ps[
        "Antennae_North.cal.lsrk.split_ddi_0_intent_OBSERVE_TARGET#ON_SOURCE_field_id_0"
    ]

    from graphviper.graph_tools.utils import make_parallel_coord

    parallel_coords = {}
    n_chunks = 4
    parallel_coords["baseline_id"] = make_parallel_coord(
        coord=ms_xds.baseline_id, n_chunks=n_chunks
    )

    n_chunks = 3
    parallel_coords["frequency"] = make_parallel_coord(
        coord=ms_xds.frequency, n_chunks=n_chunks
    )

    def my_func(input_parms):
        from xradio.vis.load_processing_set import load_processing_set
        ps = load_processing_set(
                ps_name=input_parms["input_data_name"],
                sel_parms=input_parms["data_sel"],
            )
        test_sum = 0
        for ms_xds in ps.values():
            test_sum = test_sum  + ms_xds.frequency[-1].data/(100*(input_parms['chunk_indx'][0]+input_parms['chunk_indx'][1]+1))
        return test_sum #input_parms["test_input"]

    input_parms = {}
    input_parms["test_input"] = 42
    sel_parms = {}
    sel_parms["fields"] = ["NGC4038 - Antennae North"]
    sel_parms["intents"] = ["OBSERVE_TARGET#ON_SOURCE"]
    graph = map(
        input_data_name=ps_name,
        input_data_type="processing_set",
        ps_sel_parms=sel_parms,
        parallel_coords=parallel_coords,
        func_chunk=my_func,
        input_parms=input_parms,
        client=None,
    )

    from graphviper.graph_tools import reduce
    import numpy as np

    def my_sum(graph_inputs, input_parms):
        return np.sum(graph_inputs) + input_parms["test_input"]

    input_parms = {}
    input_parms["test_input"] = 5
    graph_reduce = reduce(
        graph, my_sum, input_parms, mode="tree"
    )  # mode "tree","single_node"

    assert dask.compute(graph_reduce)[0][0][0] == 44544495255.635056