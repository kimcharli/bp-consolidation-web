import { queryFetch } from "./common.js";

const template = document.createElement("template");
template.innerHTML = `
    <style>
        table {
            width: 100%;
            border: 1px solid black;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            text-align: left;
        }
        th {
            background-color: var(--global-th-color);
        }
    </style>

    <table>
    <tr>
        <th>Main Blueprint</th>
        <th>ToR Blueprint</th>
    </tr>
    <tr>
        <td id="main_bp">Masin</th>
        <td id="tor_bp">AZ</th>
    </tr>
    <tr>
        <td>box</th>
        <td>
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:lucid="lucid" width="841" height="461">
                <g transform="translate(-299.5 -39.5)" lucid:page-tab-id="0_0">
                    <path d="M320 366a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v108a6 6 0 0 1-6 6H326a6 6 0 0 1-6-6z" stroke="#3a414a" fill="#fff"/>
                    <use xlink:href="#a" transform="matrix(1,0,0,1,325,365) translate(131.45679012345678 59.02777777777778)"/>
                    <path d="M800 366a6 6 0 0 1 6-6h308a6 6 0 0 1 6 6v108a6 6 0 0 1-6 6H806a6 6 0 0 1-6-6z" stroke="#3a414a" fill="#fff"/>
                    <use xlink:href="#b" transform="matrix(1,0,0,1,805,365) translate(131.45679012345678 59.02777777777778)"/>
                    <path d="M320 66a6 6 0 0 1 6-6h788a6 6 0 0 1 6 6v108a6 6 0 0 1-6 6H326a6 6 0 0 1-6-6z" stroke="#3a414a" fill="#fff"/>
                    <use xlink:href="#c" transform="matrix(1,0,0,1,325,65) translate(347.5308641975309 59.02777777777778)"/>
                    <path d="M728.16 420.5h-17v-1h17z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path fill="#3a414a"/>
                    <path stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M799.5 420.5h-.33v-1h.33z" fill="#3a414a"/>
                    <path d="M799.52 420.52h-.35v-.04h.3v-.96h-.3v-.04h.36z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#d" transform="matrix(1,0,0,1,640.1604938271605,409.3333333333333) translate(0 14.222222222222223)"/>
                    <use xlink:href="#d" transform="matrix(1,0,0,1,728.1604938271605,409.3333333333333) translate(0 14.222222222222223)"/>
                    <path d="M379.17 359h-1v-11h1zm0-32.33h-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M379.17 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M379.2 181.04h-1.06v-.56h1.05zm-1-.5v.45h.94v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M379.17 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M379.2 359.52h-1.06v-.56h1.05zm-1-.5v.46h.94V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#e" transform="matrix(1,0,0,1,343.1604930445876,326.6656666666667) translate(0 14.222222222222223)"/>
                    <path d="M440.5 359h-1v-17.67h1zm0-39h-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M440.5 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M440.52 181.04h-1.04v-.56h1.04zm-1-.5v.45h.96v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M440.5 359.5h-1v-.5h1z" fill="#3a414a"/><path d="M440.52 359.52h-1.04v-.56h1.04zm-1-.5v.46h.96V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#f" transform="matrix(1,0,0,1,404.49382637791996,320) translate(0 14.222222222222223)"/>
                    <path d="M524.5 359h-1v-11h1zm297.33-144.98l-.08 1-.23 1-.4.93-.53.87-.67.78-.77.66-.88.53-.94.38-1 .24-1 .08H530.03l-.88.07-.84.2-.8.33-.73.45-.66.56-.55.67-.45.73-.33.8-.2.84-.07.88v100.65h-1v-100.7l.08-1 .24-.98.4-.95.52-.87.66-.78.78-.66.87-.53.94-.38.98-.24 1-.08H815.3l.9-.07.83-.2.8-.33.74-.45.65-.56.56-.67.45-.73.33-.8.2-.84.07-.88V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M524.5 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M524.52 359.52h-1.04v-.56h1.04zm-1-.5v.46h.96V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M821.83 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M821.86 181.04h-1.05v-.56h1.06zm-1-.5v.45h.95v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#g" transform="matrix(1,0,0,1,488.49382743106827,326.66666666666663) translate(0 14.222222222222223)"/>
                    <path d="M567.17 359h-1v-31h1zM892.5 244.02l-.08 1-.24 1-.4.93-.52.87-.66.78-.78.66-.87.53-.94.38-.98.24-1 .08H572.7l-.9.07-.83.2-.8.33-.74.45-.65.56-.56.67-.45.73-.33.8-.2.84-.07.88v50.65h-1v-50.7l.08-1 .23-.98.4-.95.53-.87.67-.78.77-.66.88-.53.94-.38 1-.24 1-.08h313.32l.88-.07.84-.2.8-.33.73-.45.66-.56.55-.67.45-.73.33-.8.2-.84.07-.88V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M892.5 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M892.52 181.04h-1.04v-.56h1.04zm-1-.5v.45h.96v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M567.17 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M567.2 359.52h-1.06v-.56h1.05zm-1-.5v.46h.94V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#h" transform="matrix(1,0,0,1,531.1604984267346,306.6666666666667) translate(0 14.222222222222223)"/>
                    <path d="M1052.5 359h-1v-39h1zm0-60.33h-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M1052.5 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M1052.53 181.04h-1.06v-.56h1.06zm-1-.5v.45h.94v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M1052.5 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M1052.53 359.52h-1.06v-.56h1.06zm-1-.5v.46h.94V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#h" transform="matrix(1,0,0,1,1016.493825193477,298.66666666666663) translate(0 14.222222222222223)"/>
                    <path d="M1003.17 359h-1v-9.67h1zm0-31h-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M1003.17 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M1003.2 181.04h-1.06v-.56h1.05zm-1-.5v.45h.94v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M1003.17 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M1003.2 359.52h-1.06v-.56h1.05zm-1-.5v.46h.94V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#g" transform="matrix(1,0,0,1,967.1604918601445,328) translate(0 14.222222222222223)"/>
                    <path d="M931.17 359h-1v-11h1zm0-32.33h-1v-5.34h1zm-248-62.7l.07.9.2.83.33.8.45.73.56.66.65.55.74.45.8.33.84.2.9.07h236l.98.08 1 .24.94.4.87.52.76.66.67.78.53.87.4.94.23.98.07 1V300h-1v-23.98l-.07-.88-.2-.84-.33-.8-.46-.73-.55-.66-.65-.55-.74-.45-.8-.33-.83-.2-.88-.07h-236l-1-.08-1-.24-.93-.4-.88-.52-.77-.66-.66-.78-.53-.87-.4-.94-.23-.98-.07-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M931.17 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M931.2 359.52h-1.06v-.56h1.05zm-1-.5v.46h.94V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M683.17 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M683.2 181.04h-1.06v-.56h1.05zm-1-.5v.45h.94v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#f" transform="matrix(1,0,0,1,895.1604936648421,300) translate(0 14.222222222222223)"/>
                    <path d="M900.5 359h-1v-11h1zm0-32.33h-1v-5.34h1zm-262.67-32.7l.07.9.2.83.33.8.46.73.55.66.65.55.74.45.8.33.83.2.88.07h250.67l1 .08 1 .24.43.18h-1.3v.64l-.3-.07-.87-.07H643.3l-.98-.08-1-.24-.94-.4-.87-.52-.76-.66-.67-.78-.53-.87-.4-.94-.23-.98-.07-1V181h1z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M637.83 181h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M637.86 181.04h-1.05v-.56h1.06zm-1-.5v.45h.95v-.47z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <path d="M900.5 359.5h-1v-.5h1z" fill="#3a414a"/>
                    <path d="M900.52 359.52h-1.04v-.56h1.04zm-1-.5v.46h.96V359z" stroke="#3a414a" stroke-width=".05" fill="#3a414a"/>
                    <use xlink:href="#e" transform="matrix(1,0,0,1,864.4938317600836,326.66666666666663) translate(0 14.222222222222223)"/>
                    <defs>
                        <path fill="#3a414a" d="M24 0v-261h32V0H24" id="i"/>
                        <path fill="#3a414a" d="M100-194c63 0 86 42 84 106H49c0 40 14 67 53 68 26 1 43-12 49-29l28 8c-11 28-37 45-77 45C44 4 14-33 15-96c1-61 26-98 85-98zm52 81c6-60-76-77-97-28-3 7-6 17-6 28h103" id="j"/>
                        <path fill="#3a414a" d="M141-36C126-15 110 5 73 4 37 3 15-17 15-53c-1-64 63-63 125-63 3-35-9-54-41-54-24 1-41 7-42 31l-33-3c5-37 33-52 76-52 45 0 72 20 72 64v82c-1 20 7 32 28 27v20c-31 9-61-2-59-35zM48-53c0 20 12 33 32 33 41-3 63-29 60-74-43 2-92-5-92 41" id="k"/>
                        <path fill="#3a414a" d="M101-234c-31-9-42 10-38 44h38v23H63V0H32v-167H5v-23h27c-7-52 17-82 69-68v24" id="l"/>
                        <path fill="#3a414a" d="M27 0v-27h64v-190l-56 39v-29l58-41h29v221h61V0H27" id="m"/>
                        <g id="a">
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,0,0)" xlink:href="#i"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,4.876543209876543,0)" xlink:href="#j"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,17.22222222222222,0)" xlink:href="#k"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,29.5679012345679,0)" xlink:href="#l"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,35.74074074074074,0)" xlink:href="#m"/>
                        </g>
                        <path fill="#3a414a" d="M101-251c82-7 93 87 43 132L82-64C71-53 59-42 53-27h129V0H18c2-99 128-94 128-182 0-28-16-43-45-43s-46 15-49 41l-32-3c6-41 34-60 81-64" id="n"/>
                        <g id="b">
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,0,0)" xlink:href="#i"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,4.876543209876543,0)" xlink:href="#j"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,17.22222222222222,0)" xlink:href="#k"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,29.5679012345679,0)" xlink:href="#l"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,35.74074074074074,0)" xlink:href="#n"/>
                        </g>
                        <path fill="#3a414a" d="M30 0v-248h33v221h125V0H30" id="o"/>
                        <path fill="#3a414a" d="M30 0v-248h187v28H63v79h144v27H63v87h162V0H30" id="p"/>
                        <path fill="#3a414a" d="M205 0l-28-72H64L36 0H1l101-248h38L239 0h-34zm-38-99l-47-123c-12 45-31 82-46 123h93" id="q"/>
                        <path fill="#3a414a" d="M63-220v92h138v28H63V0H30v-248h175v28H63" id="r"/>
                        <path fill="#3a414a" d="M16-82v-28h88v28H16" id="s"/>
                        <path fill="#3a414a" d="M143 4C61 4 22-44 18-125c-5-107 100-154 193-111 17 8 29 25 37 43l-32 9c-13-25-37-40-76-40-61 0-88 39-88 99 0 61 29 100 91 101 35 0 62-11 79-27v-45h-74v-28h105v86C228-13 192 4 143 4" id="t"/>
                        <path fill="#3a414a" d="M185-189c-5-48-123-54-124 2 14 75 158 14 163 119 3 78-121 87-175 55-17-10-28-26-33-46l33-7c5 56 141 63 141-1 0-78-155-14-162-118-5-82 145-84 179-34 5 7 8 16 11 25" id="u"/>
                        <g id="c">
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,0,0)" xlink:href="#o"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,12.345679012345679,0)" xlink:href="#p"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,27.160493827160494,0)" xlink:href="#q"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,41.9753086419753,0)" xlink:href="#r"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,55.49382716049382,0)" xlink:href="#s"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,62.8395061728395,0)" xlink:href="#t"/>
                            <use transform="matrix(0.06172839506172839,0,0,0.06172839506172839,80.12345679012344,0)" xlink:href="#u"/>
                        </g>
                        <path fill="#333" d="M185-48c-13 30-37 53-82 52C43 2 14-33 14-96s30-98 90-98c62 0 83 45 84 108H66c0 31 8 55 39 56 18 0 30-7 34-22zm-45-69c5-46-57-63-70-21-2 6-4 13-4 21h74" id="v"/>
                        <path fill="#333" d="M115-3C79 11 28 4 28-45v-112H4v-33h27l15-45h31v45h36v33H77v99c-1 23 16 31 38 25v30" id="w"/>
                        <path fill="#333" d="M14-72v-43h91v43H14" id="x"/>
                        <path fill="#333" d="M101-251c68 0 84 54 84 127C185-50 166 4 99 4S15-52 14-124c-1-75 17-127 87-127zm-1 216c37-5 36-46 36-89s4-89-36-89c-39 0-36 45-36 89 0 43-3 85 36 89" id="y"/>
                        <path fill="#333" d="M4 7l51-268h42L46 7H4" id="z"/>
                        <path fill="#333" d="M139-81c0-46-55-55-73-27H18l9-140h149v37H72l-4 63c44-38 133-4 122 66C201 21 21 35 11-62l49-4c5 18 15 30 39 30 26 0 40-18 40-45" id="A"/>
                        <path fill="#333" d="M128-127c34 4 56 21 59 58 7 91-148 94-172 28-4-9-6-17-7-26l51-5c1 24 16 35 40 36 23 0 39-12 38-36-1-31-31-36-65-34v-40c32 2 59-3 59-33 0-20-13-33-34-33s-33 13-35 32l-50-3c6-44 37-68 86-68 50 0 83 20 83 66 0 35-22 52-53 58" id="B"/>
                        <g id="d">
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,0,0)" xlink:href="#v"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,9.876543209876544,0)" xlink:href="#w"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,15.753086419753087,0)" xlink:href="#x"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,21.629629629629633,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,31.506172839506174,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,36.44444444444445,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,46.320987654320994,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,51.25925925925927,0)" xlink:href="#A"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,61.13580246913581,0)" xlink:href="#B"/>
                        </g>
                        <path fill="#333" d="M165-50V0h-47v-50H5v-38l105-160h55v161h33v37h-33zm-47-37l2-116L46-87h72" id="C"/>
                        <path fill="#333" d="M138-131c27 9 52 24 51 61 0 53-36 74-89 74S11-19 11-69c0-35 22-54 51-61-78-25-46-121 38-121 51 0 83 19 83 66 0 30-18 49-45 54zm-38-16c24 0 32-13 32-36 1-23-11-34-32-34-22 0-33 12-32 34 0 22 9 36 32 36zm1 116c27 0 37-17 37-43 0-25-13-39-39-39-24 0-37 15-37 40 0 27 11 42 39 42" id="D"/>
                        <g id="e">
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,0,0)" xlink:href="#v"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,9.876543209876544,0)" xlink:href="#w"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,15.753086419753087,0)" xlink:href="#x"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,21.629629629629633,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,31.506172839506174,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,36.44444444444445,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,46.320987654320994,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,51.25925925925927,0)" xlink:href="#C"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,61.13580246913581,0)" xlink:href="#D"/>
                        </g>
                        <path fill="#333" d="M99-251c69 0 84 53 88 123 5 99-61 162-144 118-15-8-21-25-26-45l46-6c4 31 50 33 63 7 7-15 12-36 12-60-9 18-29 28-54 28-48 0-72-32-72-82 0-55 31-83 87-83zm-1 128c24 0 37-16 37-39 0-27-10-51-37-51-25 0-35 19-35 45 0 25 10 45 35 45" id="E"/>
                        <g id="f">
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,0,0)" xlink:href="#v"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,9.876543209876544,0)" xlink:href="#w"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,15.753086419753087,0)" xlink:href="#x"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,21.629629629629633,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,31.506172839506174,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,36.44444444444445,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,46.320987654320994,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,51.25925925925927,0)" xlink:href="#C"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,61.13580246913581,0)" xlink:href="#E"/>
                        </g>
                        <g id="g">
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,0,0)" xlink:href="#v"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,9.876543209876544,0)" xlink:href="#w"/><use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,15.753086419753087,0)" xlink:href="#x"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,21.629629629629633,0)" xlink:href="#y"/><use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,31.506172839506174,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,36.44444444444445,0)" xlink:href="#y"/><use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,46.320987654320994,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,51.25925925925927,0)" xlink:href="#A"/><use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,61.13580246913581,0)" xlink:href="#y"/>
                        </g>
                        <path fill="#333" d="M23 0v-37h61v-169l-59 37v-38l62-41h46v211h57V0H23" id="F"/>
                        <g id="h">
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,0,0)" xlink:href="#v"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,9.876543209876544,0)" xlink:href="#w"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,15.753086419753087,0)" xlink:href="#x"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,21.629629629629633,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,31.506172839506174,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,36.44444444444445,0)" xlink:href="#y"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,46.320987654320994,0)" xlink:href="#z"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,51.25925925925927,0)" xlink:href="#A"/>
                            <use transform="matrix(0.04938271604938272,0,0,0.04938271604938272,61.13580246913581,0)" xlink:href="#F"/>
                        </g>
                    </defs>
                </g>
            </svg>
        </td>
    </tr>
    
    </table>
`

class AccessSwitches extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: "open" });
        this.shadowRoot.appendChild(template.content.cloneNode(true));

        // this.shadowRoot.querySelector("button").addEventListener("click", () => {
        //     this.dispatchEvent(new CustomEvent("onEdit", { detail: this.accessSwitch }));
        // });
    }

    fetch_blueprint() {
        queryFetch( `
            query {
                fetchBlueprints {                
                    label
                    role
                    id
                }
            }
        `)
        .then(data => {
            data.data.fetchBlueprints.forEach(element => {
                this.shadowRoot.getElementById(element.role).innerHTML = element.label;
                this.shadowRoot.getElementById(element.role).style.backgroundColor = 'var(--global-warning-color)';
            })
        });
    }

    connectedCallback() {
        this.fetch_blueprint();
    }

    set accessSwitch(accessSwitch) {
        this._accessSwitch = accessSwitch;
        this.render();
    }

    get accessSwitch() {
        return this._accessSwitch;
    }

    render() {
        this.shadowRoot.querySelector("td").innerHTML = this.accessSwitch.name;
    }
}
customElements.define("access-switches", AccessSwitches);