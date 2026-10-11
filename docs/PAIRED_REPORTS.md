# Offline comparison paired intervals

`amo compare` includes a `paired_intervals` field for every unique policy pair if at least three unique seeds are available. Confidence intervals use paired percentile bootstrap resampling of the same-seed best objective differences, with fixed sampling seed. Missing observations are not imputed. **The default objective is a synthetic fixture**, and no drug optimization performance claim is supported. For fewer than three seeds the interval list is empty. Real model comparisons must separately pass provenance and cost integrity gates.
