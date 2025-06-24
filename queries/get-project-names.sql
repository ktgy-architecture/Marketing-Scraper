SELECT
    DISTINCT(PR.WBS1) AS WBS1,
    PR.Name,
    PR.LongName
FROM PR
    LEFT JOIN ProjectCustomTabFields
        ON PR.WBS1 = ProjectCustomTabFields.WBS1
WHERE (PR.WBS1 LIKE '%.00' OR PR.WBS1 LIKE '%.10')
    AND (PR.Stage LIKE '%WDEF%' OR PR.Stage = '06')
    AND PR.WBS2 = ' '
    AND PR.WBS1 NOT LIKE 'P%'
    AND PR.WBS1 NOT LIKE 'M%'
    AND PR.WBS1 NOT LIKE '00000%';