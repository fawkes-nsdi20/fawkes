#! /bin/bash
# set -x

RECDIR="$(pwd)/examples/yahoo"
OUTDIR="$RECDIR/replay"
MM_TOOLS_DIR="$(pwd)/mm_tools"

init_ver='v0'
target_ver='v1'


get_main_html() {
    # $1 -> recorded_dir
    # $2 -> output_file
    local recorded_dir=$1
    local output_file=$2
    local grepped=($(grep -rl "GET / " $recorded_dir))
    if [[ ${#grepped[@]} -eq 0 ]]; then
        echo "[Error] Failed to grep the top-level HTML for $recorded_dir."
        return 10
    fi
    if [[ ${#grepped[@]} -ne 1 ]]; then
        echo "[Error] More than one file was grepped by '/' as top-level object."
        return 10
    fi
    main_file=${grepped[0]}

    temp="$OUTDIR/temp" #$(dirname $output_file)
    chunked="$OUTDIR/chunked"

    headers=$("$MM_TOOLS_DIR"/protototext $main_file $temp)
    if [[ -z "$headers" ]]; then
        echo "[Error] Failed to decode the top-level object ($main_file)."
        return 11
    fi
    # echo "headers=$headers"
    # split headers by '*' to see if chunked, gzipped or brotlied
    IFS='*' read -ra array <<< "$headers";
    # remove prefix from each part -> ${FOO#prefix}
    is_chunked="${array[2]#chunked=}"
    is_gzipped="${array[3]#gzipped=}"
    is_brotlied="${array[4]#brotlied=}"

    if [[ "$is_chunked" == 'true' ]]; then
        (mv $temp $chunked \
        && python "$MM_TOOLS_DIR/unchunk.py" $chunked $temp \
        && rm $chunked) \
            || { ec=$?;
                 echo "[Error] Failed to unchunk $main_file.";
                 return $ec; }
    fi

    if [[ "$is_gzipped" == 'true' ]]; then
        (mv $temp $temp.gz \
             && gunzip $temp.gz) \
            || { ec=$?;
                 echo "[Error] Failed to gunzip $main_file.";
                 return $ec; }
    fi

    if [[ "$is_brotlied" == 'true' ]]; then
        (mv $temp $temp.br \
        && brotli -d $temp.br 2>/dev/null \
        && rm $temp.br) \
            || { ec=$?;
                 echo "[Error] Failed to unbrotli $main_file";
                 return $ec; }
    fi

    mv $temp "$output_file"
    return 0
}

make_fawkes_default() {
    # Given the original target dir, static_template and dynamic_patch
    # creates two directories, default and Fawkes,
    # assuming we are in $OUTDIR at this moment

    # first remove existing .br files if any exists
    rm -rf *.br
    brotli "$static_template" &>/dev/null
    static_template="$static_template".br

    brotli "$dynamic_patch" &>/dev/null
    dynamic_patch="$dynamic_patch".br

    #########################DEFAULT#########################
    default_dir="$page_name"-default
    rm -rf "$default_dir" && cp -r "$target" "$default_dir"

    # updates the cacheable object headers to one year for $default_dir
    # the trailing '/' is critical for cachingheaders
    cacheables=$("$MM_TOOLS_DIR"/cachingheaders "$default_dir/" 2> invalid_files)
    invalids=$(cat invalid_files)
    if [[ -n "$invalids" ]]; then
        echo "$invalids" | xargs rm
    fi
    rm invalid_files

    #########################FAWKES#########################
    fawkes_dir="$page_name"-fawkes
    rm -rf "$fawkes_dir" && cp -r "$default_dir" "$fawkes_dir"
    local main_file=$(grep -rl "GET / " "$fawkes_dir")
    if [[ -z "$main_file" ]]; then
        # This should not happen. Since this is a copy of $target
        # in case $target has no or more than one top-level it has exited.
        echo "[Error] Failed to grep the top-level HTML for $fawkes_dir."
        return 100
    fi

    # copy the main html protobuf file as a base for update.json
    cp "$main_file" "$fawkes_dir"/save.myJSON
    "$MM_TOOLS_DIR"/jsonheaders "$dynamic_patch" "$fawkes_dir"/save.myJSON >/dev/null

    # all the other cacheable object headers are already updated,
    # we just need to update the main file which is also done in commontoproto
    "$MM_TOOLS_DIR"/commontoproto "$static_template" "$main_file"

    # clean up the folder before returning
    # rm ./*.html
    rm ./*.br
}

prepare_page () {
    # $1 -> Example domain name
    page_name=$1

    init_html="$OUTDIR/$page_name-$init_ver.html"
    get_main_html $initial $init_html \
        || { rc=$?; return $rc; }

    target_html="$OUTDIR/$page_name-$target_ver.html"
    get_main_html $target $target_html \
        || { rc=$?; return $rc; }

    # paths to Fawkes outputs (static template & dynamic patch) under OUTDIR.
    static_template="$OUTDIR/$page_name"_template.html
    dynamic_patch="$OUTDIR/update.json"

    # run our adapted tree matching algorithm on these two top-level HTMLs
    # third arg should be path to static_template
    cd TreeMatching
    python3.7 treematching/run_apted.py \
              $init_html $target_html $static_template
    rc=$?
    if [[ $rc != 0 ]]; then
        echo "Failed to generate static template HTML for $page_name"
        cd ../
        return $rc
    fi

    # again run out adapted tree matching to generate the dynamic patch
    # an extra fourth argument ('json') is needed.
    python3.7 treematching/run_apted.py \
              $static_template $target_html $dynamic_patch json
    rc=$?
    if [[ $rc != 0 ]]; then
        echo "Failed to generate dynamic patches for $page_name"
        cd ../
        return $rc
    fi
    # stepping out of TreeMatching directory
    cd ../

    # rm -f $OUTDIR/*.tree

    # The version of static template which includes the JS patcher
    static_template="${static_template%.html}"_patched.html

    # Saving the last working directory, before stepping in OUTDIR
    last_wd=$(pwd)
    cd "$OUTDIR"

    # Creates the Fawkes version of target html (as a Mahimahi directory)
    make_fawkes_default
    rc=$?
    if [[ $rc != 0 ]]; then
        echo "Failed to create fawkes/default directories for $page_name"
        cd "$last_wd"
        return $rc
    fi
    cd "$last_wd"
    return 0
}

# Make sure TreeMatching is placed next to this script
if [[ ! -d "TreeMatching" ]]; then
    echo '[Error] Could not find TreeMatching next to this script.'
    exit 1
fi

# initial and target versions of the recorded page
initial="$RECDIR/record/$init_ver"
target="$RECDIR/record/$target_ver"

if [[ ! -d "$initial" || ! -d "$target" ]]; then
    echo '[Error] Invalid example directory is given.'
    echo 'Please use either of the provided directories under examples.'
    exit 1
elif [[ -z "$(ls -A $initial 2>/dev/null)" ]]; then
    echo "[Error] $(basename $initial) should not be empty."
    exit 1
elif [[ -z "$(ls -A $target 2>/dev/null)" ]]; then
    echo "[Error] $(basename $target) should not be empty."
    exit 1
fi

# make output directory if it does not exist
mkdir -p "$OUTDIR"
page_name=$(basename "$RECDIR")
prepare_page $page_name
exit
